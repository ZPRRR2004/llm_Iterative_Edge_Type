"""Strict structural and source-evidence validation, independent of the model."""
import json


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def keys(value, expected):
    require(isinstance(value, dict) and set(value) == set(expected.split()),
            f"Expected exactly fields: {expected}")


def string(value):
    require(isinstance(value, str) and bool(value.strip()), "Expected non-empty string")


def flags(value):
    require(isinstance(value, list) and all(isinstance(x, str) for x in value),
            "review_flags must be an array of strings")


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def constant(value):
        raise Invalid(f"Invalid JSON constant: {value}")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def root_query(value):
    keys(value, "title query review_flags")
    string(value['title'])
    string(value['query'])
    flags(value['review_flags'])


def alignment_assignments(value, tool_calls):
    keys(value, 'assignments')
    require(isinstance(value['assignments'], list), 'assignments must be an array')
    ids = []
    for item in value['assignments']:
        keys(item, 'tool_call_id start_anchor')
        string(item['tool_call_id'])
        anchor = item['start_anchor']
        require(anchor is None or (isinstance(anchor, str) and bool(anchor)),
                'start_anchor must be a non-empty string or null')
        ids.append(item['tool_call_id'])
    require(ids == [call['tool_call_id'] for call in tool_calls],
            'Assignments must match input calls in order')

