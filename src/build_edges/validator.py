"""Strict validators for edge types and all three LLM response schemas."""
import re


EDGE_TYPE_FIELDS = {
    'name',
    'definition',
    'source_description',
    'target_description',
}
EDGE_NAME = re.compile(r'^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$')


class ValidationError(ValueError):
    pass


def _exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValidationError(f'{label} 必须且只能包含字段：{sorted(expected)}')


def validate_edge_type(value, label='Edge Type'):
    _exact_keys(value, EDGE_TYPE_FIELDS, label)
    for field in EDGE_TYPE_FIELDS:
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValidationError(f'{label}.{field} 必须是非空字符串')
    if not EDGE_NAME.fullmatch(value['name']):
        raise ValidationError(
            f'{label}.name 必须使用大写字母、数字和下划线：{value["name"]!r}')
    return value


def validate_edge_type_list(values, label):
    if not isinstance(values, list):
        raise ValidationError(f'{label} 必须是数组')
    names = []
    for index, value in enumerate(values):
        validate_edge_type(value, f'{label}[{index}]')
        names.append(value['name'])
    if len(names) != len(set(names)):
        raise ValidationError(f'{label} 中存在重复类型名称')
    return values


def validate_registry(registry):
    return validate_edge_type_list(registry, 'Registry')


def validate_discovery(value):
    _exact_keys(value, {'candidate_edge_types'}, 'Discovery 输出')
    validate_edge_type_list(value['candidate_edge_types'], 'candidate_edge_types')
    return value


def validate_comparison(value, candidates, registry):
    _exact_keys(value, {'existing', 'new', 'uncertain'}, 'Comparison 输出')
    for key in ('existing', 'new', 'uncertain'):
        if not isinstance(value[key], list):
            raise ValidationError(f'comparison.{key} 必须是数组')

    candidate_by_name = {item['name']: item for item in candidates}
    registry_names = {item['name'] for item in registry}
    classified = []

    for index, item in enumerate(value['existing']):
        _exact_keys(item, {'candidate_name', 'matched_existing_name'},
                    f'existing[{index}]')
        for field in ('candidate_name', 'matched_existing_name'):
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValidationError(f'existing[{index}].{field} 必须是非空字符串')
        if item['candidate_name'] not in candidate_by_name:
            raise ValidationError(f'未知候选类型：{item["candidate_name"]}')
        if item['matched_existing_name'] not in registry_names:
            raise ValidationError(f'未知 Registry 类型：{item["matched_existing_name"]}')
        classified.append(item['candidate_name'])

    for category in ('new', 'uncertain'):
        validate_edge_type_list(value[category], category)
        for item in value[category]:
            if item['name'] not in candidate_by_name:
                raise ValidationError(f'{category} 包含未知候选类型：{item["name"]}')
            classified.append(item['name'])

    expected = list(candidate_by_name)
    if len(classified) != len(set(classified)):
        raise ValidationError('同一候选类型被重复分类')
    if set(classified) != set(expected):
        missing = sorted(set(expected) - set(classified))
        extra = sorted(set(classified) - set(expected))
        raise ValidationError(f'候选分类不完整；缺失={missing}，额外={extra}')
    if not registry and (value['existing'] or value['uncertain'] or
                         {item['name'] for item in value['new']} != set(expected)):
        raise ValidationError('Registry 为空时，所有候选类型必须分类为 new')
    return value


def validate_review(value, candidates, registry):
    _exact_keys(value, {'accepted_edge_types'}, 'Review 输出')
    accepted = validate_edge_type_list(value['accepted_edge_types'],
                                       'accepted_edge_types')
    registry_names = {item['name'] for item in registry}
    conflicts = sorted(registry_names & {item['name'] for item in accepted})
    if conflicts:
        raise ValidationError(f'Review 接受了 Registry 中已有的名称：{conflicts}')
    if not candidates and accepted:
        raise ValidationError('候选列表为空时不能接受新增类型')
    return value


def validate_registry_update(registry_snapshot, accepted_types):
    validate_registry(registry_snapshot)
    validate_edge_type_list(accepted_types, 'accepted_edge_types')
    existing = {item['name'] for item in registry_snapshot}
    conflicts = sorted(existing & {item['name'] for item in accepted_types})
    if conflicts:
        raise ValidationError(f'新增类型名称与 Registry 冲突：{conflicts}')
    return True
