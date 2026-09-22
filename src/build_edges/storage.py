"""Atomic persistence for registries, execution state, calls, batches, and manifests."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from src.deepseek_client import encoded

from .validator import validate_edge_type_list, validate_registry


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(text, encoding='utf-8')
    for attempt in range(5):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.05 * (attempt + 1))


def atomic_save_json(path, value):
    atomic_write_text(path, encoded(value) + '\n')


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class Storage:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.registry_path = self.output_dir / 'edge_type_registry.json'
        self.state_path = self.output_dir / 'execution_state.json'
        self.manifest_path = self.output_dir / 'window_manifest.json'

    def initialize(self, manifest):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        occupied = [path for path in self.output_dir.iterdir()]
        if occupied:
            raise ValueError(f'输出目录必须为空；如需恢复请使用 --resume：{self.output_dir}')
        atomic_save_json(self.registry_path, [])
        atomic_save_json(self.manifest_path, manifest)

    def verify_manifest(self, current):
        if not self.manifest_path.is_file():
            raise ValueError('恢复失败：缺少 window_manifest.json')
        saved = load_json(self.manifest_path)
        if saved != current:
            raise ValueError('恢复失败：输入 Window 文件集合、顺序或内容已发生变化')

    def save_registry(self, registry):
        validate_registry(registry)
        atomic_save_json(self.registry_path, registry)

    def load_registry(self):
        if not self.registry_path.is_file():
            raise ValueError('缺少 edge_type_registry.json')
        value = load_json(self.registry_path)
        validate_registry(value)
        return value

    def save_state(self, state):
        atomic_save_json(self.state_path, state)

    def load_state(self):
        if not self.state_path.is_file():
            raise ValueError('恢复失败：缺少 execution_state.json')
        value = load_json(self.state_path)
        required = {
            'next_window_index', 'completed_windows', 'current_batch_index',
            'completed_windows_in_batch', 'prompt_version', 'next_stage', 'status',
            'config',
        }
        if not isinstance(value, dict) or not required <= set(value):
            raise ValueError('execution_state.json 格式无效')
        if value['status'] not in {'running', 'waiting_for_enter', 'completed', 'failed'}:
            raise ValueError('execution_state.json status 无效')
        return value

    def run_dir(self, record):
        return self.output_dir / 'runs' / record.run_name

    def save_window_metadata(self, record, metadata):
        atomic_save_json(self.run_dir(record) / 'metadata.json', metadata)

    def load_window_metadata(self, record):
        path = self.run_dir(record) / 'metadata.json'
        return load_json(path) if path.is_file() else None

    def save_stage_call(self, record, stage, call_record):
        directory = self.run_dir(record)
        request_path = directory / f'{stage}_request.json'
        response_path = directory / f'{stage}_response.json'
        previous_calls = []
        if request_path.is_file() and response_path.is_file():
            old_request = load_json(request_path)
            old_response = load_json(response_path)
            previous_calls = list(old_response.pop('previous_calls', []))
            previous_calls.append({
                'request': old_request,
                'response': old_response,
            })
        request = {
            'stage': stage,
            'window_file': record.path.name,
            'prompt_version': call_record['prompt_version'],
            'model': call_record['model'],
            'started_at': call_record['started_at'],
            **call_record['request'],
        }
        response = {
            'stage': stage,
            'window_file': record.path.name,
            'prompt_version': call_record['prompt_version'],
            'model': call_record['model'],
            'succeeded': call_record['succeeded'],
            'completed_at': call_record['completed_at'],
            'duration_seconds': call_record['duration_seconds'],
            'attempt_count': len(call_record['attempts']),
            'attempts': call_record['attempts'],
            'parsed_response': call_record.get('parsed_response'),
            'previous_calls': previous_calls,
        }
        atomic_save_json(request_path, request)
        atomic_save_json(response_path, response)

    def load_stage_result(self, record, stage):
        path = self.run_dir(record) / f'{stage}_response.json'
        if not path.is_file():
            raise ValueError(f'恢复失败：缺少 {record.run_name}/{stage}_response.json')
        value = load_json(path)
        if not value.get('succeeded') or not isinstance(value.get('parsed_response'), dict):
            raise ValueError(f'恢复失败：{record.run_name} 的 {stage} 尚未成功')
        return value['parsed_response']

    def save_batch(self, *, batch_index, start_window, end_window,
                   prompt_version, registry_before, registry_after):
        directory = self.output_dir / 'batches' / f'batch_{batch_index:04d}'
        before_names = {item['name'] for item in registry_before}
        new_types = [item for item in registry_after if item['name'] not in before_names]
        atomic_save_json(directory / 'registry_before.json', registry_before)
        atomic_save_json(directory / 'registry_after.json', registry_after)
        atomic_save_json(directory / 'newly_accepted_edge_types.json', new_types)
        metadata = {
            'batch_index': batch_index,
            'start_window': start_window,
            'end_window': end_window,
            'prompt_version': prompt_version,
            'new_edge_type_count': len(new_types),
            'registry_size': len(registry_after),
            'saved_at': utc_now(),
        }
        atomic_save_json(directory / 'batch_metadata.json', metadata)
        atomic_write_text(directory / 'review_packet.md',
                          self._review_packet(metadata, new_types, registry_after))
        return directory / 'review_packet.md', new_types

    @staticmethod
    def _review_packet(metadata, new_types, registry):
        lines = [
            f'# 第 {metadata["batch_index"]} 批 Edge Type Discovery 结果', '',
            '## 一、批次信息', '',
            f'处理 Window：{metadata["start_window"]}–{metadata["end_window"]}',
            f'Prompt 版本：{metadata["prompt_version"]}',
            f'本批新增边类型：{len(new_types)}',
            f'当前边类型总数：{len(registry)}', '',
            '## 二、本批新增边类型', '',
        ]
        if not new_types:
            lines.extend(['本批没有接受新的边类型。', ''])
        else:
            for item in new_types:
                lines.extend(Storage._edge_markdown(item))
        lines.extend(['## 三、当前完整 Registry', ''])
        if not registry:
            lines.append('Registry 当前为空。')
        else:
            for item in registry:
                lines.extend(Storage._edge_markdown(item))
        return '\n'.join(lines).rstrip() + '\n'

    @staticmethod
    def _edge_markdown(item):
        return [
            f'### {item["name"]}', '',
            f'name: {item["name"]}', '',
            f'definition: {item["definition"]}', '',
            f'source_description: {item["source_description"]}', '',
            f'target_description: {item["target_description"]}', '',
        ]

    def reconstruct_registry(self, records, completed_windows, save=True):
        registry = []
        names = set()
        for record in records[:completed_windows]:
            metadata = self.load_window_metadata(record)
            if not metadata or metadata.get('status') != 'completed':
                raise ValueError(f'恢复失败：Window {record.run_name} 未完整提交')
            accepted = metadata.get('accepted_edge_types')
            validate_edge_type_list(
                accepted, f'{record.run_name}.accepted_edge_types')
            for item in accepted:
                if item['name'] in names:
                    raise ValueError(f'恢复失败：重复 Registry 类型 {item["name"]}')
                names.add(item['name'])
                registry.append(item)
        validate_registry(registry)
        if save:
            self.save_registry(registry)
        return registry
