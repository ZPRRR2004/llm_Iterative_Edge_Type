"""Split preprocessed trajectories into self-contained analysis windows."""

from .splitter import split_trajectory
from .token_counter import count_core_tokens, count_text_tokens, serialize_events
from .window_builder import build_window

__all__ = [
    'build_window',
    'count_core_tokens',
    'count_text_tokens',
    'serialize_events',
    'split_trajectory',
]
