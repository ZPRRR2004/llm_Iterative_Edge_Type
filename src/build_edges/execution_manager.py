"""Coordinate stage calls, commits, batches, prompt editing, and resume."""
import copy

from .comparison import run_comparison
from .discovery import run_discovery
from .llm_client import StageCallError
from .registry import update_registry
from .review import run_review
from .storage import utc_now
from .validator import (validate_comparison, validate_discovery,
                        validate_registry_update, validate_review)
from .window_loader import serialize_context_window


STAGE_ORDER = ('discovery', 'comparison', 'review', 'commit')


def _save_failed_call(storage, record, stage, metadata, error):
    if isinstance(error, StageCallError):
        storage.save_stage_call(record, stage, error.record)
    metadata.update({
        'status': 'failed',
        'failed_stage': stage,
        'error': str(error),
        'updated_at': utc_now(),
    })
    storage.save_window_metadata(record, metadata)


def _complete_stage(storage, record, stage, parsed, call_record,
                    metadata, state, next_stage):
    storage.save_stage_call(record, stage, call_record)
    if stage not in metadata['completed_stages']:
        metadata['completed_stages'].append(stage)
    metadata.update({'status': 'running', 'updated_at': utc_now()})
    storage.save_window_metadata(record, metadata)
    state.update({'next_stage': next_stage, 'status': 'running'})
    storage.save_state(state)
    return parsed


def process_window(*, record, registry, llm_client, prompt_bundle,
                   prompt_version, storage, state):
    registry_snapshot = copy.deepcopy(registry)
    context_window = serialize_context_window(record)
    metadata = storage.load_window_metadata(record)
    if metadata is None:
        metadata = {
            'window_file': record.path.name,
            'trajectory_id': record.trajectory_id,
            'window_id': record.window_id,
            'global_index': record.global_index,
            'prompt_version': prompt_version,
            'registry_snapshot': registry_snapshot,
            'completed_stages': [],
            'accepted_edge_types': [],
            'status': 'running',
            'created_at': utc_now(),
            'updated_at': utc_now(),
        }
        storage.save_window_metadata(record, metadata)
    else:
        if metadata.get('prompt_version') != prompt_version:
            raise ValueError(f'{record.run_name} 的 Prompt 版本与执行状态不一致')
        if metadata.get('registry_snapshot') != registry_snapshot:
            raise ValueError(f'{record.run_name} 的 Registry 快照与恢复状态不一致')

    next_stage = state['next_stage']
    if next_stage not in STAGE_ORDER:
        raise ValueError(f'未知恢复阶段：{next_stage}')

    if STAGE_ORDER.index(next_stage) <= STAGE_ORDER.index('discovery'):
        try:
            discovery, call_record = run_discovery(
                context_window=context_window, llm_client=llm_client,
                prompts=prompt_bundle, window_name=record.run_name,
                prompt_version=prompt_version)
            discovery = _complete_stage(
                storage, record, 'discovery', discovery, call_record,
                metadata, state, 'comparison')
        except Exception as exc:
            _save_failed_call(storage, record, 'discovery', metadata, exc)
            raise
    else:
        discovery = storage.load_stage_result(record, 'discovery')
        validate_discovery(discovery)

    candidates = discovery['candidate_edge_types']
    if STAGE_ORDER.index(state['next_stage']) <= STAGE_ORDER.index('comparison'):
        try:
            comparison, call_record = run_comparison(
                candidate_types=candidates,
                existing_registry=registry_snapshot,
                llm_client=llm_client, prompts=prompt_bundle,
                window_name=record.run_name, prompt_version=prompt_version)
            comparison = _complete_stage(
                storage, record, 'comparison', comparison, call_record,
                metadata, state, 'review')
        except Exception as exc:
            _save_failed_call(storage, record, 'comparison', metadata, exc)
            raise
    else:
        comparison = storage.load_stage_result(record, 'comparison')
        validate_comparison(comparison, candidates, registry_snapshot)

    if STAGE_ORDER.index(state['next_stage']) <= STAGE_ORDER.index('review'):
        try:
            review, call_record = run_review(
                context_window=context_window, candidate_types=candidates,
                comparison_result=comparison,
                existing_registry=registry_snapshot,
                llm_client=llm_client, prompts=prompt_bundle,
                window_name=record.run_name, prompt_version=prompt_version)
            review = _complete_stage(
                storage, record, 'review', review, call_record,
                metadata, state, 'commit')
        except Exception as exc:
            _save_failed_call(storage, record, 'review', metadata, exc)
            raise
    else:
        review = storage.load_stage_result(record, 'review')
        validate_review(review, candidates, registry_snapshot)

    accepted_types = review['accepted_edge_types']
    validate_registry_update(registry_snapshot, accepted_types)
    updated_registry = update_registry(registry_snapshot, accepted_types)
    metadata.update({
        'status': 'completed',
        'failed_stage': None,
        'error': None,
        'accepted_edge_types': accepted_types,
        'registry_size_after': len(updated_registry),
        'completed_at': utc_now(),
        'updated_at': utc_now(),
    })
    storage.save_window_metadata(record, metadata)
    return {
        'discovery': discovery,
        'comparison': comparison,
        'review': review,
        'updated_registry': updated_registry,
    }


def wait_for_prompt_edit(*, batch_index, completed_windows, total_windows,
                         batch_new_types, registry, prompt_manager,
                         output_dir, input_func=input):
    print('\n' + '=' * 60)
    print(f'【Build Edges】第 {batch_index} 批处理完成')
    print('=' * 60)
    print(f'\n处理进度：{completed_windows} / {total_windows} 个 Window')
    print(f'本批新增边类型：{batch_new_types} 个')
    print(f'当前边类型总数：{len(registry)} 个')
    print(f'当前 Prompt 版本：{prompt_manager.current_version}')
    print(f'\n边类型库：\n  {output_dir / "edge_type_registry.json"}')
    packet = output_dir / 'batches' / f'batch_{batch_index:04d}' / 'review_packet.md'
    print(f'\n本批结果：\n  {packet}')
    print('\n可修改的 Prompt 文件：\n')
    for path in prompt_manager.editable_prompt_paths:
        print(f'  {path}')

    while True:
        input_func('\n请查看本批结果并按需修改 Prompt 文件。'
                   '\n修改完成后，请按 Enter 继续执行...')
        try:
            changed, version = prompt_manager.save_next_from_disk()
        except Exception as exc:
            print(f'\n【Prompt 检查失败】{exc}')
            print('请修正 Prompt 文件后重新按 Enter。')
            continue
        if changed:
            print(f'\n已检测到 Prompt 修改。\n新 Prompt 版本：{version}')
        else:
            print(f'\nPrompt 内容未发生变化，已保存下一批 Prompt 快照：{version}。')
        print(f'\n当前 Registry 已保留，共 {len(registry)} 个边类型。')
        print(f'开始处理第 {batch_index + 1} 批 Window...')
        return version


def _continue_after_feedback(state, registry, records, config,
                             prompt_manager, storage, input_func):
    batch_start = state['completed_windows'] - state['completed_windows_in_batch']
    registry_before = storage.reconstruct_registry(records, batch_start, save=False)
    batch_new_types = len(registry) - len(registry_before)
    version = wait_for_prompt_edit(
        batch_index=state['current_batch_index'],
        completed_windows=state['completed_windows'],
        total_windows=len(records),
        batch_new_types=batch_new_types,
        registry=registry,
        prompt_manager=prompt_manager,
        output_dir=storage.output_dir,
        input_func=input_func)
    state.update({
        'current_batch_index': state['current_batch_index'] + 1,
        'completed_windows_in_batch': 0,
        'prompt_version': version,
        'next_stage': 'discovery',
        'status': 'running',
    })
    storage.save_state(state)


def process_all_windows(*, records, manifest, config, prompt_manager,
                        llm_client, storage, resume=False, input_func=input):
    if resume:
        storage.verify_manifest(manifest)
        state = storage.load_state()
        if state['config'] != config:
            raise ValueError('恢复失败：当前 Config 与首次运行时的 Config 不一致')
        registry = storage.reconstruct_registry(records, state['completed_windows'])
        prompt_manager.resume(state['prompt_version'])
        if state['status'] == 'completed':
            print('该输出目录中的所有 Context Window 已处理完成。')
            return registry
        if state['status'] == 'waiting_for_enter':
            _continue_after_feedback(
                state, registry, records, config,
                prompt_manager, storage, input_func)
        elif state['status'] == 'failed':
            state['status'] = 'running'
            storage.save_state(state)
    else:
        storage.initialize(manifest)
        version = prompt_manager.initialize()
        state = {
            'next_window_index': 0,
            'completed_windows': 0,
            'current_batch_index': 1,
            'completed_windows_in_batch': 0,
            'prompt_version': version,
            'next_stage': 'discovery',
            'status': 'running',
            'config': copy.deepcopy(config),
        }
        storage.save_state(state)
        registry = []

    interval = config['human_feedback_interval']
    batch_start_count = state['completed_windows'] - state['completed_windows_in_batch']
    batch_registry_before = storage.reconstruct_registry(
        records, batch_start_count, save=False)

    while state['next_window_index'] < len(records):
        record = records[state['next_window_index']]
        prompts = prompt_manager.get_active_prompts()
        try:
            result = process_window(
                record=record, registry=registry,
                llm_client=llm_client, prompt_bundle=prompts,
                prompt_version=prompt_manager.current_version,
                storage=storage, state=state)
        except Exception as exc:
            state['status'] = 'failed'
            storage.save_state(state)
            print(f'\n【Build Edges 失败】Window：{record.run_name}')
            print(f'原因：{exc}')
            print('已保存执行状态。修复问题后使用 --resume 继续。')
            raise

        registry = result['updated_registry']
        storage.save_registry(registry)
        state.update({
            'next_window_index': record.global_index + 1,
            'completed_windows': record.global_index + 1,
            'completed_windows_in_batch': state['completed_windows_in_batch'] + 1,
            'next_stage': 'discovery',
            'status': 'running',
        })
        storage.save_state(state)

        all_finished = state['completed_windows'] == len(records)
        batch_finished = state['completed_windows_in_batch'] == interval
        if batch_finished or all_finished:
            batch_start = state['completed_windows'] - state['completed_windows_in_batch'] + 1
            storage.save_batch(
                batch_index=state['current_batch_index'],
                start_window=batch_start,
                end_window=state['completed_windows'],
                prompt_version=prompt_manager.current_version,
                registry_before=batch_registry_before,
                registry_after=registry)
            if all_finished:
                state.update({'status': 'completed', 'next_stage': 'discovery'})
                storage.save_state(state)
                break
            state['status'] = 'waiting_for_enter'
            storage.save_state(state)
            _continue_after_feedback(
                state, registry, records, config,
                prompt_manager, storage, input_func)
            batch_registry_before = copy.deepcopy(registry)

    print('\n全部 Context Window 处理完成。')
    print(f'最终边类型总数：{len(registry)} 个')
    print(f'最终 Registry：{storage.registry_path}')
    return registry
