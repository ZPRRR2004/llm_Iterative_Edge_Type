"""Normalize Terminus 2 trajectories from the Terminal-Bench 2.0 corpus."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from ..deepseek_client import save
from .validate import alignment_assignments, require, root_query, strict_json, string
from .profile import EXPECTED_AGENT, EXPECTED_SCHEMA, NAME as ADAPTER_NAME


OBSERVATION_WARNING_PREFIX = (
    'Previous response had warnings:\n'
    'WARNINGS: - Extra text detected before JSON object\n'
    '- Extra text detected after JSON object\n\n'
)


def clean_observation_content(content):
    """Remove the known ATIF parser-warning wrapper only when it is a prefix."""
    if content.startswith(OBSERVATION_WARNING_PREFIX):
        return content[len(OBSERVATION_WARNING_PREFIX):]
    crlf_prefix = OBSERVATION_WARNING_PREFIX.replace('\n', '\r\n')
    if content.startswith(crlf_prefix):
        return content[len(crlf_prefix):]
    return content


def compact_calls(tool_calls):
    """Keep only the information needed to match calls to a combined observation."""
    result = []
    for call in tool_calls:
        call_input = call['arguments']
        if call['tool_name'] == 'bash_command' and isinstance(call_input.get('keystrokes'), str):
            call_input = call_input['keystrokes']
        result.append({'tool_call_id': call['tool_call_id'], 'tool_name': call['tool_name'],
                       'input': call_input})
    return result


def _anchor_mismatch_detail(combined, anchor):
    """Locate a unique copied prefix and report the first changed source character."""
    for length in range(len(anchor), 0, -1):
        prefix = anchor[:length]
        position = combined.find(prefix)
        if position < 0 or combined.find(prefix, position + 1) >= 0:
            continue
        offset = length
        while (offset < len(anchor) and position + offset < len(combined) and
               anchor[offset] == combined[position + offset]):
            offset += 1
        expected = (repr(combined[position + offset])
                    if position + offset < len(combined) else '<end of source>')
        actual = repr(anchor[offset]) if offset < len(anchor) else '<end of anchor>'
        return (f'closest exact prefix begins at source character {position}; first '
                f'difference at source character {position + offset}: expected source '
                f'{expected}, got anchor {actual}')
    return 'no unique exact prefix locates a nearby source position'


def materialize_alignment(plan, tool_calls, contents):
    """Locate short model-selected anchors, then slice exact text from the source."""
    alignment_assignments(plan, tool_calls)
    combined = ''.join(contents)
    positions = []
    for item in plan['assignments']:
        anchor = item['start_anchor']
        if anchor is None:
            positions.append(None)
            continue
        matches = []
        cursor = 0
        while True:
            position = combined.find(anchor, cursor)
            if position < 0:
                break
            matches.append(position)
            cursor = position + 1
        preview = repr(anchor[:80] + ('...' if len(anchor) > 80 else ''))
        if not matches:
            require(False,
                    f'{item["tool_call_id"]}: start_anchor not found exactly in source; '
                    f'{_anchor_mismatch_detail(combined, anchor)}; copy whitespace and '
                    f'line breaks exactly; anchor={preview}')
        require(len(matches) == 1,
                f'{item["tool_call_id"]}: start_anchor is not unique; matches at source '
                f'characters {matches[:8]}; extend the exact anchor')
        positions.append(matches[0])

    observed = [(index, position) for index, position in enumerate(positions)
                if position is not None]
    require(observed, 'At least one tool call must have a non-null start_anchor')
    first_index, first_position = observed[0]
    require(first_position == 0,
            f'{plan["assignments"][first_index]["tool_call_id"]}: first non-empty '
            f'start_anchor begins at source character {first_position}, expected 0')
    for (previous_index, previous), (index, position) in zip(observed, observed[1:]):
        require(position > previous,
                f'{plan["assignments"][index]["tool_call_id"]}: start_anchor at source '
                f'character {position} must follow '
                f'{plan["assignments"][previous_index]["tool_call_id"]} at {previous}')

    assignments = []
    next_positions = {
        index: (observed[offset + 1][1] if offset + 1 < len(observed) else len(combined))
        for offset, (index, _) in enumerate(observed)
    }
    for index, item in enumerate(plan['assignments']):
        position = positions[index]
        raw = '' if position is None else combined[position:next_positions[index]]
        assignments.append({'tool_call_id': item['tool_call_id'], 'observation_raw': raw})
    require(''.join(item['observation_raw'] for item in assignments) == combined,
            'Program-sliced observations do not cover the complete source')
    return assignments


def align_observations_by_source_call_id(tool_calls, observations):
    """Return exact local assignments when every observation names its source call."""
    if not observations or any(item.get('source_call_id') is None for item in observations):
        return None

    grouped = {call['tool_call_id']: [] for call in tool_calls}
    for item in observations:
        source_call_id = item['source_call_id']
        require(source_call_id in grouped,
                f'observation source_call_id {source_call_id!r} does not match a tool call '
                'in the same step')
        grouped[source_call_id].append(item['content'])
    return [
        {'tool_call_id': call['tool_call_id'],
         'observation_raw': ''.join(grouped[call['tool_call_id']])}
        for call in tool_calls
    ]


def print_alignment(event, contents, split, mode):
    """Show a compact observation-assignment summary without printing its contents."""
    name = f"split-{event['step_id']}"
    total = sum(len(item) for item in contents)
    assignments = ', '.join(
        f'{item["tool_call_id"]}={len(item["observation_raw"])}字符'
        for item in split['assignments']
    ) or '无'
    print(f'[{name}] 结果（{mode}）：{len(event["tool_calls"])} 个 tool call，'
          f'{len(contents)} 段 observation，共 {total} 字符；分配：{assignments}',
          flush=True)


def load(path):
    path = Path(path)
    raw = path.read_bytes()
    trace = strict_json(raw.decode('utf-8'))
    require(isinstance(trace, dict) and isinstance(trace.get('schema_version'), str), 'Missing ATIF schema_version')
    require(trace['schema_version'] == EXPECTED_SCHEMA,
            f'{ADAPTER_NAME} adapter requires {EXPECTED_SCHEMA}')
    agent = trace.get('agent')
    agent_name = agent.get('name') if isinstance(agent, dict) else None
    require(agent_name == EXPECTED_AGENT,
            f"{ADAPTER_NAME} adapter requires agent.name={EXPECTED_AGENT!r}; "
            f"got {agent_name!r}")
    require(isinstance(trace.get('steps'), list) and bool(trace['steps']), 'Missing steps')
    seen = set()
    for step in trace['steps']:
        require(isinstance(step, dict), 'Each step must be an object')
        sid = step.get('step_id')
        require(type(sid) in (int, str) and sid not in seen, 'Missing or duplicate step_id')
        seen.add(sid)
        require(step.get('source') in ('user', 'agent'), 'Unsupported step source')
        require(isinstance(step.get('message'), str), 'message must be text')
        calls = step.get('tool_calls', [])
        require(isinstance(calls, list), 'tool_calls must be an array')
        for call in calls:
            require(isinstance(call, dict), 'Tool call must be an object')
            string(call.get('function_name'))
            require(isinstance(call.get('arguments'), dict), 'Tool arguments must be an object')
        observation = step.get('observation') or {}
        require(isinstance(observation, dict) and isinstance(observation.get('results', []), list), 'Invalid observation')
        for result in observation.get('results', []):
            require(isinstance(result, dict) and isinstance(result.get('content'), str), 'Only textual observation content is supported')
            if 'source_call_id' in result:
                require(isinstance(result['source_call_id'], str) and
                        bool(result['source_call_id'].strip()),
                        'observation source_call_id must be non-empty text')
    require(trace['steps'][0]['source'] == 'user', 'Trajectory must start with the user task')
    require(not trace['steps'][0].get('tool_calls') and not trace['steps'][0].get('observation'), 'First user step cannot contain actions/observations')
    return trace, {'filename': path.name, 'sha256': hashlib.sha256(raw).hexdigest(),
                   'adapter': ADAPTER_NAME}


def prepare(trace):
    counts = Counter(c.get('tool_call_id') for s in trace['steps'] for c in s.get('tool_calls', [])
                     if isinstance(c.get('tool_call_id'), str))
    reserved = set(counts)
    events, flags = [], []
    for i, step in enumerate(trace['steps'][1:], 1):
        event = {'event_id': f'event-{i:04d}', 'step_id': step['step_id'], 'source': step['source'],
                 'thought': step['message'], 'tool_calls': []}
        for j, original in enumerate(step.get('tool_calls', []), 1):
            cid = original.get('tool_call_id')
            if not isinstance(cid, str) or not cid.strip() or counts[cid] != 1:
                fallback = f"{step['step_id']}:tool:{j}"
                while fallback in reserved:
                    fallback += ':fallback'
                reserved.add(fallback)
                flags.append(f"step {step['step_id']}: 缺失或重复 tool_call_id {cid!r}，改用 {fallback}")
                cid = fallback
            arguments = copy.deepcopy(original['arguments'])
            if original['function_name'] == 'bash_command':
                arguments.pop('duration', None)
            event['tool_calls'].append({'tool_call_id': cid, 'tool_name': original['function_name'],
                                        'arguments': arguments})
        observations = [
            {'source_call_id': r.get('source_call_id'),
             'content': clean_observation_content(r['content'])}
            for r in (step.get('observation') or {}).get('results', [])
        ]
        events.append((event, observations))
    return events, flags


def normalize(trace, source, client):
    result = client.ask('root', ['extract_root_v1'], 'extract_root_user',
                        {'first_user_message_json': trace['steps'][0]['message']}, root_query)
    prepared, flags = prepare(trace)
    flags.extend(result['review_flags'])
    output = {'source': source, 'query': {'title': result['title'], 'text': result['query'],
              'source_ref': {'step_id': trace['steps'][0]['step_id'], 'field': 'message'},
              'source_raw': trace['steps'][0]['message']}, 'events': [], 'review_flags': flags}
    for event, observations in prepared:
        contents = [item['content'] for item in observations]
        nonempty_contents = [item for item in contents if item]
        source_id_assignments = (align_observations_by_source_call_id(
            event['tool_calls'], observations) if event['source'] == 'agent' else None)
        if source_id_assignments is not None:
            assignments = source_id_assignments
            mode = '按 source_call_id 本地直接对齐，未调用模型'
        elif event['source'] == 'agent' and len(event['tool_calls']) == 1:
            assignments = [{'tool_call_id': event['tool_calls'][0]['tool_call_id'],
                            'observation_raw': ''.join(contents)}]
            mode = '本地直接对齐，未调用模型'
        elif event['source'] == 'agent' and event['tool_calls'] and nonempty_contents:
            print(f'[split-{event["step_id"]}] 需要模型判断：{len(event["tool_calls"])} 个 tool call，'
                  f'{len(contents)} 段 observation', flush=True)
            model_input = {'tool_calls': compact_calls(event['tool_calls']),
                           'combined_observation': ''.join(contents)}
            plan = client.ask(f"split-{event['step_id']}",
                ['align_observations_v1'],
                'align_observations_user',
                {'step_input_json': model_input},
                lambda value: materialize_alignment(value, event['tool_calls'], contents),
                thinking=False, retries=2)
            assignments = materialize_alignment(plan, event['tool_calls'], contents)
            mode = '模型拆分，程序校验完整覆盖'
        else:
            require(not nonempty_contents,
                    f'step {event["step_id"]}: observation exists without an assignable agent tool call')
            assignments = [{'tool_call_id': c['tool_call_id'], 'observation_raw': ''}
                           for c in event['tool_calls']]
            mode = '无需模型拆分'
        split = {'assignments': assignments}
        print_alignment(event, contents, split, mode)
        for call, assigned in zip(event['tool_calls'], assignments):
            call['observation'] = {'raw': assigned['observation_raw']}
        output['events'].append(event)
        save(client.directory / 'checkpoint.json', {'stage': 'normalizing', 'source': source,
                                                    'last_step_id': event['step_id']})
    return output
