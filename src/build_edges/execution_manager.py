"""Coordinate stage calls, commits, batch feedback, and resume."""
import copy

from .comparison import run_comparison
from .discovery import run_discovery
from .llm_client import StageCallError
from .registry import apply_registry_revision, apply_review_result
from .registry_revision import run_registry_revision
from .review import run_review
from .storage import utc_now
from .validator import (validate_comparison, validate_discovery,
                        validate_registry_revision_plan,
                        validate_review)
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
            'revised_existing_edge_types': [],
            'accepted_edge_type_count': 0,
            'revised_existing_edge_type_count': 0,
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
        validate_review(review, candidates, comparison, registry_snapshot)

    accepted_types = review['accepted_edge_types']
    validate_review(review, candidates, comparison, registry_snapshot)
    updated_registry = apply_review_result(registry_snapshot, review)
    registry_by_name = {edge['name']: edge for edge in registry_snapshot}
    revision_history = [
        {
            'original_name': item['original_name'],
            'original_edge_type': copy.deepcopy(
                registry_by_name[item['original_name']]),
            'revised_edge_type': copy.deepcopy(item['revised_edge_type']),
        }
        for item in review['revised_existing_edge_types']
    ]
    metadata.update({
        'status': 'completed',
        'failed_stage': None,
        'error': None,
        'accepted_edge_types': accepted_types,
        'revised_existing_edge_types': revision_history,
        'accepted_edge_type_count': len(accepted_types),
        'revised_existing_edge_type_count': len(revision_history),
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


def print_window_summary(record, result):
    comparison = result['comparison']
    review = result['review']
    revisions = review['revised_existing_edge_types']
    print(f'\n【Build Edges】Window {record.global_index + 1} 处理完成')
    print(f'\nDiscovery 候选类型：{len(result["discovery"]["candidate_edge_types"])}')
    print('Comparison：')
    for key in ('existing', 'new', 'uncertain'):
        print(f'  {key.upper()}：{len(comparison[key])}')
    print('\nReview：')
    print(f'  接受新增类型：{len(review["accepted_edge_types"])}')
    print(f'  修订已有类型：{len(revisions)}')
    print(f'\n当前 Registry 类型总数：{len(result["updated_registry"])}')
    renamed = [item for item in revisions
               if item['original_name'] != item['revised_edge_type']['name']]
    if renamed:
        print('\n【本轮已有类型修订】\n')
        for item in renamed:
            print(f'{item["original_name"]}\n    → {item["revised_edge_type"]["name"]}')


def _feedback_mode_label(mode):
    return 'Manual Prompt' if mode == 'manual_prompt' else 'Registry Feedback'


def print_startup(*, total_windows, config, prompt_version, registry):
    print('\n' + '=' * 60)
    print('【Build Edges】启动')
    print('=' * 60)
    print(f'\nContext Window 数量：{total_windows}')
    print(f'人工反馈间隔：每 {config["human_feedback_interval"]} 个 Window')
    print(f'反馈模式：{_feedback_mode_label(config["feedback_mode"])}')
    print(f'当前 Prompt 版本：{prompt_version}')
    print(f'当前 Registry：{len(registry)} 个边类型')
    print('\n开始处理...')


def _print_batch_summary(*, batch_index, completed_windows, total_windows,
                         batch_new_types, registry, prompt_version,
                         feedback_mode, output_dir):
    print('\n' + '=' * 60)
    print(f'【Build Edges】第 {batch_index} 批处理完成')
    print('=' * 60)
    print(f'\n处理进度：{completed_windows} / {total_windows} 个 Window')
    print(f'本批新增边类型：{batch_new_types} 个')
    print(f'当前边类型总数：{len(registry)} 个')
    print(f'当前 Prompt 版本：{prompt_version}')
    print(f'反馈模式：{_feedback_mode_label(feedback_mode)}')
    print(f'\n当前 Registry：\n  {output_dir / "edge_type_registry.json"}')
    packet = output_dir / 'batches' / f'batch_{batch_index:04d}' / 'review_packet.md'
    print(f'\n本批结果：\n  {packet}')


def wait_for_prompt_edit(*, batch_index, completed_windows, total_windows,
                         batch_new_types, registry, prompt_manager,
                         output_dir, input_func=input):
    _print_batch_summary(
        batch_index=batch_index, completed_windows=completed_windows,
        total_windows=total_windows, batch_new_types=batch_new_types,
        registry=registry, prompt_version=prompt_manager.current_version,
        feedback_mode='manual_prompt', output_dir=output_dir)
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
        return version, changed


def read_human_feedback(input_func=input):
    print('\n请查看当前边类型发现结果。')
    print('\n请输入你对当前 Edge Type Registry 的自然语言反馈。')
    print('支持输入多行内容。')
    print('输入完成后，请单独输入 END 并按 Enter。\n')
    lines = []
    while True:
        line = input_func('> ')
        if line.strip() == 'END':
            break
        lines.append(line)
    return '\n'.join(lines).strip()


def _revision_counts(revision_plan):
    counts = {name: 0 for name in ('KEEP', 'DELETE', 'REVISE', 'MERGE')}
    for item in revision_plan['revisions']:
        counts[item['operation']] += 1
    return counts


def print_registry_revision_summary(*, registry_before, revision_plan,
                                    registry_after, output_dir, batch_index):
    counts = _revision_counts(revision_plan)
    print('\n' + '=' * 60)
    print('【Registry Revision】完成')
    print('=' * 60)
    print(f'\n反馈前边类型数量：{len(registry_before)}')
    print(f'反馈后边类型数量：{len(registry_after)}')
    print('\n本轮操作统计：\n')
    print(f'  保留 KEEP：      {counts["KEEP"]}')
    print(f'  删除 DELETE：    {counts["DELETE"]}')
    print(f'  修订 REVISE：    {counts["REVISE"]}')
    print(f'  合并 MERGE：     {counts["MERGE"]}')
    directory = output_dir / 'batches' / f'batch_{batch_index:04d}'
    print(f'\nRevision Plan：\n  {directory / "registry_revision_plan.json"}')
    print(f'\n修改后 Registry：\n  {output_dir / "edge_type_registry.json"}')

    revised = [item for item in revision_plan['revisions']
               if item['operation'] == 'REVISE']
    merged = [item for item in revision_plan['revisions']
              if item['operation'] == 'MERGE']
    deleted = [item for item in revision_plan['revisions']
               if item['operation'] == 'DELETE']
    if revised:
        print('\n【REVISE】\n')
        for item in revised:
            print(f'{item["original_name"]}\n  → {item["revised_edge_type"]["name"]}\n')
    if merged:
        print('【MERGE】\n')
        for item in merged:
            print(f'{item["original_name"]}\n  → {item["merge_into"]}\n')
    if deleted:
        print('【DELETE】\n')
        for item in deleted:
            print(item['original_name'])


def handle_manual_prompt_feedback(*, batch_index, completed_windows,
                                  total_windows, batch_new_types, registry,
                                  prompt_manager, storage, input_func):
    version, changed = wait_for_prompt_edit(
        batch_index=batch_index, completed_windows=completed_windows,
        total_windows=total_windows, batch_new_types=batch_new_types,
        registry=registry, prompt_manager=prompt_manager,
        output_dir=storage.output_dir, input_func=input_func)
    storage.save_registry_after_feedback(batch_index, registry)
    storage.update_batch_metadata(
        batch_index, feedback_completed=True, feedback_applied=changed,
        feedback_completed_at=utc_now())
    return {'registry': registry, 'prompt_version': version}


def handle_registry_feedback(*, batch_index, completed_windows,
                             total_windows, batch_new_types, registry,
                             prompt_manager, llm_client, storage,
                             state, input_func):
    metadata = storage.load_batch_metadata(batch_index)
    if metadata.get('feedback_completed'):
        return {
            'registry': storage.load_registry_after_feedback(batch_index),
            'prompt_version': prompt_manager.current_version,
        }

    stage = state.get('pending_feedback_stage') or 'collecting_feedback'
    if stage == 'collecting_feedback':
        _print_batch_summary(
            batch_index=batch_index, completed_windows=completed_windows,
            total_windows=total_windows, batch_new_types=batch_new_types,
            registry=registry, prompt_version=prompt_manager.current_version,
            feedback_mode='registry_feedback', output_dir=storage.output_dir)
        feedback = read_human_feedback(input_func)
        storage.save_human_feedback(batch_index, feedback)
        if not feedback:
            storage.save_registry_after_feedback(batch_index, registry)
            storage.save_registry(registry)
            storage.update_batch_metadata(
                batch_index, feedback_completed=True, feedback_applied=False,
                feedback_completed_at=utc_now())
            print('\n【Registry Feedback】')
            print('\n本轮未输入修改意见。')
            print('当前 Registry 保持不变。')
            print(f'\n开始处理第 {batch_index + 1} 批 Window...')
            return {
                'registry': registry,
                'prompt_version': prompt_manager.current_version,
            }
        state.update({
            'pending_feedback_stage': 'revising_registry',
            'status': 'running',
        })
        storage.save_state(state)
    else:
        feedback = storage.load_human_feedback(batch_index)

    if state['pending_feedback_stage'] == 'revising_registry':
        plan_path = (storage.batch_dir(batch_index) /
                     'registry_revision_plan.json')
        if plan_path.is_file():
            revision_plan = storage.load_registry_revision_plan(batch_index)
            validate_registry_revision_plan(revision_plan, registry)
        else:
            try:
                revision_plan, call_record = run_registry_revision(
                    feedback, registry, llm_client, prompt_manager,
                    batch_name=f'batch_{batch_index:04d}',
                    prompt_version=prompt_manager.current_version,
                    return_call_record=True)
            except StageCallError as exc:
                storage.save_registry_revision_call(batch_index, exc.record)
                storage.save_registry_revision_error(batch_index, exc)
                raise
            except Exception as exc:
                storage.save_registry_revision_error(batch_index, exc)
                raise
            storage.save_registry_revision_call(batch_index, call_record)
            storage.save_registry_revision_plan(batch_index, revision_plan)
        state.update({
            'pending_feedback_stage': 'applying_revision',
            'status': 'running',
        })
        storage.save_state(state)
    else:
        revision_plan = storage.load_registry_revision_plan(batch_index)

    validate_registry_revision_plan(revision_plan, registry)
    revised_registry = apply_registry_revision(registry, revision_plan)
    storage.save_registry_after_feedback(batch_index, revised_registry)
    storage.save_registry(revised_registry)
    counts = _revision_counts(revision_plan)
    storage.update_batch_metadata(
        batch_index, feedback_completed=True, feedback_applied=True,
        registry_size_after_feedback=len(revised_registry),
        revision_operation_counts=counts, feedback_completed_at=utc_now())
    print_registry_revision_summary(
        registry_before=registry, revision_plan=revision_plan,
        registry_after=revised_registry, output_dir=storage.output_dir,
        batch_index=batch_index)
    print(f'\n开始处理第 {batch_index + 1} 批 Window...')
    return {
        'registry': revised_registry,
        'prompt_version': prompt_manager.current_version,
    }


def handle_batch_feedback(*, feedback_mode, batch_index, completed_windows,
                          total_windows, batch_new_types, registry,
                          prompt_manager, llm_client, storage, state,
                          input_func=input):
    if feedback_mode == 'manual_prompt':
        return handle_manual_prompt_feedback(
            batch_index=batch_index, completed_windows=completed_windows,
            total_windows=total_windows, batch_new_types=batch_new_types,
            registry=registry, prompt_manager=prompt_manager,
            storage=storage, input_func=input_func)
    if feedback_mode == 'registry_feedback':
        return handle_registry_feedback(
            batch_index=batch_index, completed_windows=completed_windows,
            total_windows=total_windows, batch_new_types=batch_new_types,
            registry=registry, prompt_manager=prompt_manager,
            llm_client=llm_client, storage=storage, state=state,
            input_func=input_func)
    raise ValueError(f'未知 feedback_mode：{feedback_mode}')


def _continue_after_feedback(state, registry, records, config,
                             prompt_manager, llm_client, storage, input_func):
    batch_start = state['completed_windows'] - state['completed_windows_in_batch']
    registry_before = storage.reconstruct_registry(records, batch_start, save=False)
    batch_new_types = len(registry) - len(registry_before)
    try:
        result = handle_batch_feedback(
            feedback_mode=state['feedback_mode'],
            batch_index=state['current_batch_index'],
            completed_windows=state['completed_windows'],
            total_windows=len(records), batch_new_types=batch_new_types,
            registry=registry, prompt_manager=prompt_manager,
            llm_client=llm_client, storage=storage, state=state,
            input_func=input_func)
    except Exception as exc:
        state['status'] = 'failed'
        storage.save_state(state)
        if state['feedback_mode'] == 'registry_feedback':
            storage.save_registry_revision_error(
                state['current_batch_index'], exc)
            print('\n【Registry Revision 未完成】')
            print(f'\n原因：{exc}')
            print('\n当前 Registry 已保持原状态。')
            error_path = (storage.batch_dir(state['current_batch_index']) /
                          'registry_revision_error.json')
            print(f'Revision 失败记录已保存：\n\n  {error_path}')
            print('\n使用 --resume 继续。')
        raise
    state.update({
        'current_batch_index': state['current_batch_index'] + 1,
        'completed_windows_in_batch': 0,
        'prompt_version': result['prompt_version'],
        'next_stage': 'discovery',
        'status': 'running',
        'pending_feedback_stage': None,
    })
    storage.save_state(state)
    return result['registry']


def process_all_windows(*, records, manifest, config, prompt_manager,
                        llm_client, storage, resume=False, input_func=input):
    if resume:
        storage.verify_manifest(manifest)
        state = storage.load_state()
        saved_config = copy.deepcopy(state['config'])
        saved_config.setdefault('feedback_mode', state['feedback_mode'])
        if saved_config != config or state['feedback_mode'] != config['feedback_mode']:
            raise ValueError('恢复失败：当前 Config 与首次运行时的 Config 不一致')
        state['config'] = saved_config
        registry = storage.reconstruct_registry(records, state['completed_windows'])
        prompt_manager.resume(
            state['prompt_version'],
            allow_source_fallback=state['feedback_mode'] == 'manual_prompt')
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
            'feedback_mode': config['feedback_mode'],
            'pending_feedback_stage': None,
            'status': 'running',
            'config': copy.deepcopy(config),
        }
        storage.save_state(state)
        registry = []

    print_startup(
        total_windows=len(records), config=config,
        prompt_version=prompt_manager.current_version, registry=registry)
    if state['status'] == 'completed':
        print('该输出目录中的所有 Context Window 已处理完成。')
        return registry
    if state['status'] == 'failed':
        state['status'] = 'running'
        storage.save_state(state)
    if (state['status'] == 'waiting_for_enter' or
            state['pending_feedback_stage'] is not None):
        registry = _continue_after_feedback(
            state, registry, records, config, prompt_manager,
            llm_client, storage, input_func)

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
            'pending_feedback_stage': None,
        })
        storage.save_state(state)
        print_window_summary(record, result)

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
                registry_after=registry,
                window_records=records[batch_start - 1:state['completed_windows']],
                feedback_mode=state['feedback_mode'],
                feedback_required=not all_finished)
            if all_finished:
                state.update({
                    'status': 'completed', 'next_stage': 'discovery',
                    'pending_feedback_stage': None,
                })
                storage.save_state(state)
                break
            if state['feedback_mode'] == 'manual_prompt':
                state.update({
                    'status': 'waiting_for_enter',
                    'pending_feedback_stage': None,
                })
            else:
                state.update({
                    'status': 'running',
                    'pending_feedback_stage': 'collecting_feedback',
                })
            storage.save_state(state)
            registry = _continue_after_feedback(
                state, registry, records, config, prompt_manager,
                llm_client, storage, input_func)
            batch_registry_before = copy.deepcopy(registry)

    print('\n全部 Context Window 处理完成。')
    print(f'最终边类型总数：{len(registry)} 个')
    print(f'最终 Registry：{storage.registry_path}')
    return registry
