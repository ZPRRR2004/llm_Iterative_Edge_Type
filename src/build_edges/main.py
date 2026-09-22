"""Command-line entry point for iterative semantic Edge Type discovery."""
import argparse
import os
import re
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.build_edges.execution_manager import process_all_windows
    from src.build_edges.llm_client import BuildEdgesLLM
    from src.build_edges.prompt_loader import PromptManager
    from src.build_edges.storage import Storage
    from src.build_edges.window_loader import load_windows, manifest
else:
    from .execution_manager import process_all_windows
    from .llm_client import BuildEdgesLLM
    from .prompt_loader import PromptManager
    from .storage import Storage
    from .window_loader import load_windows, manifest


INTEGER_CONFIG_KEYS = {'human_feedback_interval', 'max_llm_retries'}
CONFIG_KEYS = INTEGER_CONFIG_KEYS | {'feedback_mode'}
VALID_FEEDBACK_MODES = {'manual_prompt', 'registry_feedback'}


def load_env(path):
    if not path.is_file():
        return
    for number, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].lstrip()
        key, separator, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not separator or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
            raise ValueError(f'{path}:{number}: 应为 KEY=VALUE')
        if value.startswith(('"', "'")):
            quote = value[0]
            end = value.find(quote, 1)
            if end < 0 or (value[end + 1:].strip() and
                           not value[end + 1:].strip().startswith('#')):
                raise ValueError(f'{path}:{number}: 引号值格式无效')
            value = value[1:end]
        else:
            value = re.split(r'\s+#', value, maxsplit=1)[0].rstrip()
        os.environ.setdefault(key, value)


def load_config(path):
    values = {}
    for number, raw in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        key, separator, raw_value = line.partition(':')
        key, raw_value = key.strip(), raw_value.strip()
        if not separator or key not in CONFIG_KEYS:
            raise ValueError(f'{path}:{number}: 包含不支持的配置')
        if key in values:
            raise ValueError(f'{path}:{number}: 重复配置 {key}')
        if key in INTEGER_CONFIG_KEYS:
            if not re.fullmatch(r'[+-]?\d+', raw_value):
                raise ValueError(f'{path}:{number}: {key} 必须是整数')
            values[key] = int(raw_value)
        else:
            values[key] = raw_value
    missing = CONFIG_KEYS - set(values)
    if missing:
        raise ValueError(f'{path}: 缺少配置 {sorted(missing)}')
    if values['human_feedback_interval'] <= 0:
        raise ValueError('human_feedback_interval 必须大于 0')
    if values['max_llm_retries'] < 0:
        raise ValueError('max_llm_retries 必须是非负整数')
    if values['feedback_mode'] not in VALID_FEEDBACK_MODES:
        raise ValueError(
            'feedback_mode 必须是 manual_prompt 或 registry_feedback')
    return values


def _inside(path, parent):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    return path == parent or parent in path.parents


def parse_args(argv=None):
    module_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description='迭代发现 Agent Trajectory 的可复用语义边类型')
    parser.add_argument('--input-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--config', type=Path, default=module_dir / 'config.yaml')
    parser.add_argument('--resume', action='store_true')
    return parser.parse_args(argv)


def main(argv=None, *, transport=None, input_func=input):
    args = parse_args(argv)
    module_dir = Path(__file__).resolve().parent
    try:
        if _inside(args.input_dir, module_dir) or _inside(args.output_dir, module_dir):
            raise ValueError('input-dir 和 output-dir 必须位于 src/build_edges 模块目录之外')
        load_env(module_dir.parent / '.env')
        if not os.environ.get('DEEPSEEK_API_KEY', '').strip() and transport is None:
            raise ValueError('请在 src/.env 或系统环境变量中设置 DEEPSEEK_API_KEY')
        config = load_config(args.config)
        records = load_windows(args.input_dir)
        manifest_value = manifest(records, args.input_dir)
        storage = Storage(args.output_dir)
        prompt_manager = PromptManager(module_dir / 'prompts', args.output_dir)
        if not args.resume:
            prompt_manager.validate(prompt_manager.load_from_disk())
        llm_client = BuildEdgesLLM(
            args.output_dir,
            model=os.environ.get('DEEPSEEK_MODEL') or 'deepseek-flash',
            base_url=os.environ.get('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com',
            max_retries=config['max_llm_retries'],
            transport=transport)
        process_all_windows(
            records=records, manifest=manifest_value, config=config,
            prompt_manager=prompt_manager, llm_client=llm_client,
            storage=storage, resume=args.resume, input_func=input_func)
    except Exception as exc:
        print(f'\n【Build Edges 终止】{exc}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
