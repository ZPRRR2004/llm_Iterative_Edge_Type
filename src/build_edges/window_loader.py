"""Load, validate, sort, and serialize Split context windows."""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


class WindowError(ValueError):
    pass


@dataclass(frozen=True)
class WindowRecord:
    path: Path
    data: dict
    trajectory_id: str
    window_id: str
    window_index: int
    global_index: int
    sha256: str

    @property
    def run_name(self):
        return f'{self.trajectory_id}__{self.window_id}'


def _text(value, label):
    if not isinstance(value, str):
        raise WindowError(f'{label} 必须是字符串')


def validate_window(value, filename):
    if not isinstance(value, dict):
        raise WindowError(f'{filename}: 顶层必须是对象')
    required = {
        'trajectory_id', 'window_id', 'user_query', 'previous_summary',
        'overlap', 'core', 'future_summary', 'metadata',
    }
    missing = required - set(value)
    if missing:
        raise WindowError(f'{filename}: 缺少字段 {sorted(missing)}')
    _text(value['trajectory_id'], f'{filename}.trajectory_id')
    _text(value['window_id'], f'{filename}.window_id')
    if not value['trajectory_id'].strip() or not value['window_id'].strip():
        raise WindowError(f'{filename}: trajectory_id/window_id 不能为空')
    query = value['user_query']
    if not isinstance(query, dict):
        raise WindowError(f'{filename}.user_query 必须是对象')
    _text(query.get('title'), f'{filename}.user_query.title')
    _text(query.get('text'), f'{filename}.user_query.text')
    _text(value['previous_summary'], f'{filename}.previous_summary')
    _text(value['future_summary'], f'{filename}.future_summary')

    for section in ('overlap', 'core'):
        block = value[section]
        if not isinstance(block, dict):
            raise WindowError(f'{filename}.{section} 必须是对象')
        ids, events = block.get('event_ids'), block.get('events')
        if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
            raise WindowError(f'{filename}.{section}.event_ids 必须是字符串数组')
        if not isinstance(events, list) or not all(isinstance(item, dict) for item in events):
            raise WindowError(f'{filename}.{section}.events 必须是对象数组')
        actual_ids = [event.get('event_id') for event in events]
        if actual_ids != ids:
            raise WindowError(f'{filename}.{section} 的 event_ids 与 events 不一致')
    if not value['core']['events']:
        raise WindowError(f'{filename}.core.events 不能为空')

    metadata = value['metadata']
    if not isinstance(metadata, dict):
        raise WindowError(f'{filename}.metadata 必须是对象')
    index = metadata.get('window_index')
    if not isinstance(index, int) or isinstance(index, bool) or index <= 0:
        raise WindowError(f'{filename}.metadata.window_index 必须是正整数')
    return value


def load_windows(input_dir):
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise WindowError(f'输入目录不存在：{input_dir}')
    loaded = []
    for path in input_dir.glob('*.json'):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        try:
            value = json.loads(raw.decode('utf-8'))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise WindowError(f'{path.name}: JSON 读取失败：{exc}') from exc
        validate_window(value, path.name)
        loaded.append((value['trajectory_id'], value['metadata']['window_index'],
                       value['window_id'], path, value,
                       hashlib.sha256(raw).hexdigest()))
    if not loaded:
        raise WindowError(f'输入目录中没有 Context Window JSON：{input_dir}')
    loaded.sort(key=lambda item: (item[0], item[1], item[2], item[3].name))
    seen = set()
    records = []
    for global_index, (trajectory_id, window_index, window_id, path, value, digest) in enumerate(loaded):
        identity = (trajectory_id, window_index)
        if identity in seen:
            raise WindowError(f'重复 Window：trajectory_id={trajectory_id}, index={window_index}')
        seen.add(identity)
        records.append(WindowRecord(path, value, trajectory_id, window_id,
                                    window_index, global_index, digest))
    return records


def serialize_context_window(window):
    value = window.data if isinstance(window, WindowRecord) else window
    dumps = lambda item: json.dumps(item, ensure_ascii=False, separators=(',', ':'))
    return (
        '[USER QUERY]\n\n' + dumps(value['user_query']) +
        '\n\n\n[PREVIOUS SUMMARY]\n\n' + value['previous_summary'] +
        '\n\n\n[OVERLAP EVENTS]\n\n' + dumps(value['overlap']['events']) +
        '\n\n\n[CORE EVENTS]\n\n' + dumps(value['core']['events']) +
        '\n\n\n[FUTURE SUMMARY]\n\n' + value['future_summary']
    )


def manifest(records, input_dir):
    return {
        'input_directory': str(Path(input_dir).resolve()),
        'windows': [
            {
                'global_index': record.global_index,
                'filename': record.path.name,
                'trajectory_id': record.trajectory_id,
                'window_id': record.window_id,
                'window_index': record.window_index,
                'sha256': record.sha256,
            }
            for record in records
        ],
    }
