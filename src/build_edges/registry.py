"""Persistent ordered Edge Type Registry operations."""
import copy
import json
from pathlib import Path

from .validator import validate_registry, validate_registry_update


def load_registry(output_dir):
    path = Path(output_dir) / 'edge_type_registry.json'
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding='utf-8'))
    validate_registry(value)
    return value


def update_registry(registry_snapshot, accepted_types):
    validate_registry_update(registry_snapshot, accepted_types)
    return copy.deepcopy(registry_snapshot) + copy.deepcopy(accepted_types)
