"""Persistent ordered Edge Type Registry operations."""
import copy
import json
from pathlib import Path

from .validator import (validate_registry, validate_registry_revision_plan,
                        validate_registry_update)


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


def apply_review_result(registry_snapshot, review_result):
    """Replace matched types in place, then append accepted new types."""
    revisions = {
        item['original_name']: item['revised_edge_type']
        for item in review_result['revised_existing_edge_types']
    }
    updated_registry = [
        copy.deepcopy(revisions.get(edge['name'], edge))
        for edge in registry_snapshot
    ]
    updated_registry.extend(copy.deepcopy(review_result['accepted_edge_types']))
    validate_registry(updated_registry)
    return updated_registry


def apply_registry_revision(existing_registry, revision_plan):
    """Apply a validated revision plan without depending on plan array order."""
    validate_registry_revision_plan(revision_plan, existing_registry)
    revision_by_name = {
        item['original_name']: item for item in revision_plan['revisions']
    }
    revised_registry = []
    for original_edge in existing_registry:
        revision = revision_by_name[original_edge['name']]
        operation = revision['operation']
        if operation == 'KEEP':
            revised_registry.append(copy.deepcopy(original_edge))
        elif operation == 'REVISE':
            revised_registry.append(copy.deepcopy(revision['revised_edge_type']))
        # DELETE and MERGE sources do not remain independent Registry entries.
    validate_registry(revised_registry)
    return revised_registry
