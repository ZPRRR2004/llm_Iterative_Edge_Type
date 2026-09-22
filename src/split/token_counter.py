"""Deterministic character-based token estimates used for window splitting."""
import json
import math


def serialize_events(events):
    """Serialize events exactly as used by the splitting token estimate."""
    return json.dumps(events, ensure_ascii=False, separators=(',', ':'))


def count_text_tokens(text):
    """Estimate tokens at four Unicode characters per token."""
    return math.ceil(len(text) / 4)


def count_core_tokens(events):
    """Estimate the token count of a complete serialized event array."""
    return count_text_tokens(serialize_events(events))
