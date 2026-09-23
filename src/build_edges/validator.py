"""Strict validators for Edge Types, stage responses, and revision plans."""
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


def validate_review(value, candidates, comparison, registry):
    _exact_keys(value, {'accepted_edge_types', 'revised_existing_edge_types'},
                'Review 输出')
    accepted = validate_edge_type_list(value['accepted_edge_types'],
                                       'accepted_edge_types')
    revisions = value['revised_existing_edge_types']
    if not isinstance(revisions, list):
        raise ValidationError('revised_existing_edge_types 必须是数组')
    if not candidates and (accepted or revisions):
        raise ValidationError('候选列表为空时不能新增或修订类型')

    registry_names = {item['name'] for item in registry}
    matched_names = {item['matched_existing_name']
                     for item in comparison['existing']}
    revised_by_name = {}
    for index, item in enumerate(revisions):
        label = f'revised_existing_edge_types[{index}]'
        _exact_keys(item, {'original_name', 'revised_edge_type'}, label)
        original_name = item['original_name']
        if not isinstance(original_name, str) or not original_name.strip():
            raise ValidationError(f'{label}.original_name 必须是非空字符串')
        if original_name not in registry_names:
            raise ValidationError(f'{label} 引用了未知 Registry 类型：{original_name}')
        if original_name not in matched_names:
            raise ValidationError(
                f'{label} 的原类型不在本轮 Comparison existing 匹配中：'
                f'{original_name}')
        if original_name in revised_by_name:
            raise ValidationError(f'同一已有类型被重复修订：{original_name}')
        validate_edge_type(item['revised_edge_type'],
                           f'{label}.revised_edge_type')
        revised_by_name[original_name] = item['revised_edge_type']

    final_names = [revised_by_name.get(edge['name'], edge)['name']
                   for edge in registry]
    final_names.extend(item['name'] for item in accepted)
    if len(final_names) != len(set(final_names)):
        conflicts = sorted(name for name in set(final_names)
                           if final_names.count(name) > 1)
        raise ValidationError(f'Review 更新后 Registry 类型名称冲突：{conflicts}')
    return value


def validate_registry_update(registry_snapshot, accepted_types):
    validate_registry(registry_snapshot)
    validate_edge_type_list(accepted_types, 'accepted_edge_types')
    existing = {item['name'] for item in registry_snapshot}
    conflicts = sorted(existing & {item['name'] for item in accepted_types})
    if conflicts:
        raise ValidationError(f'新增类型名称与 Registry 冲突：{conflicts}')
    return True


REVISION_OPERATIONS = {'KEEP', 'DELETE', 'REVISE', 'MERGE'}


def validate_registry_revision_plan(revision_plan, existing_registry):
    """Validate one order-independent operation for every Registry type."""
    validate_registry(existing_registry)
    _exact_keys(revision_plan, {'revisions'}, 'Registry Revision 输出')
    revisions = revision_plan['revisions']
    if not isinstance(revisions, list):
        raise ValidationError('revisions 必须是数组')

    registry_names = {item['name'] for item in existing_registry}
    revision_by_name = {}
    for index, item in enumerate(revisions):
        label = f'revisions[{index}]'
        if not isinstance(item, dict):
            raise ValidationError(f'{label} 必须是对象')
        original_name = item.get('original_name')
        operation = item.get('operation')
        if not isinstance(original_name, str) or not original_name.strip():
            raise ValidationError(f'{label}.original_name 必须是非空字符串')
        if operation not in REVISION_OPERATIONS:
            raise ValidationError(
                f'{label}.operation 必须是 KEEP、DELETE、REVISE 或 MERGE')
        if original_name not in registry_names:
            raise ValidationError(f'{label} 引用了未知原始类型：{original_name}')
        if original_name in revision_by_name:
            raise ValidationError(f'原始类型被重复处理：{original_name}')

        if operation in {'KEEP', 'DELETE'}:
            _exact_keys(item, {'original_name', 'operation'}, label)
        elif operation == 'REVISE':
            _exact_keys(
                item, {'original_name', 'operation', 'revised_edge_type'}, label)
            validate_edge_type(item['revised_edge_type'],
                               f'{label}.revised_edge_type')
        else:
            _exact_keys(item, {'original_name', 'operation', 'merge_into'}, label)
            merge_into = item['merge_into']
            if not isinstance(merge_into, str) or not merge_into.strip():
                raise ValidationError(f'{label}.merge_into 必须是非空字符串')
            if merge_into == original_name:
                raise ValidationError(f'{label} 不能合并到自身')
            if merge_into not in registry_names:
                raise ValidationError(
                    f'{label}.merge_into 引用了未知原始类型：{merge_into}')
        revision_by_name[original_name] = item

    planned_names = set(revision_by_name)
    if planned_names != registry_names:
        missing = sorted(registry_names - planned_names)
        extra = sorted(planned_names - registry_names)
        raise ValidationError(
            f'Revision Plan 未完整覆盖 Registry；缺失={missing}，额外={extra}')

    for original_name, item in revision_by_name.items():
        if item['operation'] != 'MERGE':
            continue
        target = item['merge_into']
        target_operation = revision_by_name[target]['operation']
        if target_operation not in {'KEEP', 'REVISE'}:
            raise ValidationError(
                f'{original_name} 的 MERGE 目标 {target} 必须执行 KEEP 或 REVISE')

    final_names = []
    for edge in existing_registry:
        revision = revision_by_name[edge['name']]
        if revision['operation'] == 'KEEP':
            final_names.append(edge['name'])
        elif revision['operation'] == 'REVISE':
            final_names.append(revision['revised_edge_type']['name'])
    if len(final_names) != len(set(final_names)):
        duplicates = sorted(
            name for name in set(final_names) if final_names.count(name) > 1)
        raise ValidationError(f'Revision 后类型名称不唯一：{duplicates}')
    return revision_plan
