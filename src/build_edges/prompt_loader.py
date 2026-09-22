"""Load, validate, render, version, and reload editable Build Edges prompts."""
import copy
import os
import re
import time
from pathlib import Path


PROMPT_FILES = (
    'common/granularity_examples.txt',
    'discovery/system.txt',
    'discovery/user.txt',
    'comparison/system.txt',
    'comparison/user.txt',
    'review/system.txt',
    'review/user.txt',
)
REQUIRED_VARIABLES = {
    'discovery/user.txt': {'context_window'},
    'comparison/user.txt': {'candidate_edge_types', 'existing_registry'},
    'review/user.txt': {
        'context_window', 'candidate_edge_types',
        'comparison_results', 'existing_registry',
    },
}
PLACEHOLDER = re.compile(r'{{([a-z_]+)}}')


class PromptError(ValueError):
    pass


class PromptManager:
    def __init__(self, prompt_dir, output_dir):
        self.prompt_dir = Path(prompt_dir)
        self.output_dir = Path(output_dir)
        self.current_version = None
        self.active = None

    @property
    def editable_prompt_paths(self):
        return [self.prompt_dir / relative for relative in PROMPT_FILES]

    def load_from_disk(self):
        prompts = {}
        for relative in PROMPT_FILES:
            path = self.prompt_dir / relative
            try:
                prompts[relative] = path.read_text(encoding='utf-8').strip()
            except OSError as exc:
                raise PromptError(f'文件 {path} 读取失败：{exc}') from exc
        return prompts

    def validate(self, prompts):
        if set(prompts) != set(PROMPT_FILES):
            raise PromptError('Prompt 文件集合不完整')
        for relative in PROMPT_FILES:
            if not isinstance(prompts[relative], str) or not prompts[relative].strip():
                raise PromptError(f'文件 {self.prompt_dir / relative} 不能为空')
            actual = set(PLACEHOLDER.findall(prompts[relative]))
            required = REQUIRED_VARIABLES.get(relative, set())
            missing = required - actual
            extra = actual - required
            if missing:
                names = ', '.join('{{' + name + '}}' for name in sorted(missing))
                raise PromptError(f'文件 {self.prompt_dir / relative} 缺少模板变量 {names}')
            if extra:
                names = ', '.join('{{' + name + '}}' for name in sorted(extra))
                raise PromptError(f'文件 {self.prompt_dir / relative} 包含未知模板变量 {names}')
        return prompts

    def _version_dir(self, version):
        return self.output_dir / 'prompt_versions' / version

    def _save_version(self, version, prompts):
        from .storage import atomic_write_text
        destination = self._version_dir(version)
        if destination.exists():
            raise PromptError(f'Prompt 版本目录已存在：{destination}')
        staging = destination.with_name(destination.name + '.tmp')
        if staging.exists():
            raise PromptError(f'发现未完成的 Prompt 版本目录：{staging}')
        for relative, content in prompts.items():
            atomic_write_text(staging / relative, content.rstrip() + '\n')
        for attempt in range(5):
            try:
                os.replace(staging, destination)
                return
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.05 * (attempt + 1))

    def initialize(self):
        prompts = self.validate(self.load_from_disk())
        self.current_version = 'v0001'
        self._save_version(self.current_version, prompts)
        self.active = prompts
        return self.current_version

    def resume(self, version):
        prompts = {}
        for relative in PROMPT_FILES:
            path = self._version_dir(version) / relative
            try:
                prompts[relative] = path.read_text(encoding='utf-8').strip()
            except OSError as exc:
                raise PromptError(f'历史 Prompt {path} 读取失败：{exc}') from exc
        self.validate(prompts)
        self.current_version = version
        self.active = prompts
        return version

    def get_active_prompts(self):
        if self.active is None:
            raise PromptError('尚未激活 Prompt 版本')
        return copy.deepcopy(self.active)

    def save_next_from_disk(self):
        prompts = self.validate(self.load_from_disk())
        changed = prompts != self.active
        versions = [int(path.name[1:]) for path in
                    (self.output_dir / 'prompt_versions').glob('v[0-9][0-9][0-9][0-9]')
                    if path.is_dir() and path.name[1:].isdigit()]
        version = f'v{max(versions, default=0) + 1:04d}'
        self._save_version(version, prompts)
        self.current_version = version
        self.active = prompts
        return changed, version


def render_prompt(template, values):
    def substitute(match):
        key = match.group(1)
        if key not in values:
            raise PromptError(f'缺少 Prompt 渲染值：{{{{{key}}}}}')
        return values[key]

    rendered = PLACEHOLDER.sub(substitute, template)
    unresolved = PLACEHOLDER.findall(rendered)
    if unresolved:
        raise PromptError(f'Prompt 仍有未解析变量：{unresolved}')
    return rendered


def stage_messages(prompts, stage, values):
    system = (prompts[f'{stage}/system.txt'].rstrip() + '\n\n' +
              prompts['common/granularity_examples.txt'].strip())
    user = render_prompt(prompts[f'{stage}/user.txt'], values)
    return system, user
