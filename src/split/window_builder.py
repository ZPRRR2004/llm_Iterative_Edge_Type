"""Build the stable JSON structure consumed by downstream LLM calls."""


def _event_ids(events):
    return [event['event_id'] for event in events]


def build_window(*, trajectory_id, window_id, user_query, previous_summary,
                 overlap_events, core_events, future_summary, metadata):
    return {
        'trajectory_id': trajectory_id,
        'window_id': window_id,
        'user_query': {
            'title': user_query['title'],
            'text': user_query['text'],
        },
        'previous_summary': previous_summary,
        'overlap': {
            'event_ids': _event_ids(overlap_events),
            'events': overlap_events,
        },
        'core': {
            'event_ids': _event_ids(core_events),
            'events': core_events,
        },
        'future_summary': future_summary,
        'metadata': metadata,
    }
