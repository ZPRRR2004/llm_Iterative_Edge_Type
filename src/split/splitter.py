"""Deterministically divide an event sequence into cores and overlaps."""

from .token_counter import count_core_tokens


def split_trajectory(events, config, token_counter=count_core_tokens):
    if not events:
        return []

    max_tokens = config['max_window_tokens']
    max_events = config['max_window_events']
    overlap_count = config['overlap_events']
    windows = []
    cursor = 0

    while cursor < len(events):
        core_start = cursor
        core = []

        while cursor < len(events):
            if len(core) >= max_events:
                break
            candidate = core + [events[cursor]]
            candidate_tokens = token_counter(candidate)
            if core and candidate_tokens > max_tokens:
                break
            core.append(events[cursor])
            cursor += 1

        core_end = cursor
        overlap_start = max(0, core_start - overlap_count)
        core_tokens = token_counter(core)
        windows.append({
            'window_id': f'window_{len(windows) + 1:04d}',
            'previous_events': events[:overlap_start],
            'overlap_events': events[overlap_start:core_start],
            'core_events': core,
            'future_events': events[core_end:],
            'metadata': {
                'overlap_start_index': overlap_start,
                'core_start_index': core_start,
                'core_end_index': core_end,
                'core_event_count': len(core),
                'core_tokens': core_tokens,
                'oversized': len(core) == 1 and core_tokens > max_tokens,
            },
        })

    return windows
