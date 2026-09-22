"""CLI for splitting a directory of preprocessed trajectories into windows."""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.split.splitter import split_trajectory
    from src.split.summary_generator import SummaryGenerator
    from src.split.window_builder import build_window
else:
    from .splitter import split_trajectory
    from .summary_generator import SummaryGenerator
    from .window_builder import build_window


CONFIG_KEYS = {
    'max_previous_summary_tokens',
    'max_future_summary_tokens',
    'max_window_tokens',
    'max_window_events',
    'overlap_events',
}


def load_env(path):
    """Load simple KEY=VALUE settings while preserving existing environment values."""
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
            raise ValueError(f'{path}:{number}: expected KEY=VALUE')
        if value.startswith(('"', "'")):
            quote = value[0]
            end = value.find(quote, 1)
            if end < 0 or (value[end + 1:].strip() and
                           not value[end + 1:].strip().startswith('#')):
                raise ValueError(f'{path}:{number}: invalid quoted value')
            value = value[1:end]
        else:
            value = re.split(r'\s+#', value, maxsplit=1)[0].rstrip()
        os.environ.setdefault(key, value)


def load_config(path):
    """Read the module's deliberately small integer-only YAML configuration."""
    values = {}
    for number, raw in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        key, separator, raw_value = line.partition(':')
        key, raw_value = key.strip(), raw_value.strip()
        if not separator or key not in CONFIG_KEYS or not re.fullmatch(r'[+-]?\d+', raw_value):
            raise ValueError(f'{path}:{number}: expected one supported integer setting')
        if key in values:
            raise ValueError(f'{path}:{number}: duplicate setting {key}')
        values[key] = int(raw_value)

    missing = CONFIG_KEYS - set(values)
    if missing:
        raise ValueError(f'{path}: missing settings: {", ".join(sorted(missing))}')
    if values['max_window_tokens'] <= 0 or values['max_window_events'] <= 0:
        raise ValueError('max_window_tokens and max_window_events must be greater than zero')
    for key in ('max_previous_summary_tokens', 'max_future_summary_tokens', 'overlap_events'):
        if values[key] < 0:
            raise ValueError(f'{key} must be a non-negative integer')
    return values


def validate_trajectory(value, source_file):
    if not isinstance(value, dict):
        raise ValueError(f'{source_file}: top level must be an object')
    query = value.get('query')
    if not isinstance(query, dict):
        raise ValueError(f'{source_file}: query must be an object')
    for key in ('title', 'text'):
        if not isinstance(query.get(key), str):
            raise ValueError(f'{source_file}: query.{key} must be text')
    events = value.get('events')
    if not isinstance(events, list):
        raise ValueError(f'{source_file}: events must be an array')
    seen = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f'{source_file}: events[{index}] must be an object')
        event_id = event.get('event_id')
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError(f'{source_file}: events[{index}].event_id must be non-empty text')
        if event_id in seen:
            raise ValueError(f'{source_file}: duplicate event_id {event_id!r}')
        seen.add(event_id)
    return query, events


def safe_stem(stem):
    safe = re.sub(r'[^A-Za-z0-9._-]+', '_', stem).strip('._') or 'trajectory'
    return safe


def output_stems(files):
    """Create deterministic, collision-free safe names for input files."""
    result = {}
    used = set()
    for path in files:
        candidate = safe_stem(path.stem)
        if candidate in used:
            digest = hashlib.sha256(path.name.encode('utf-8')).hexdigest()[:8]
            candidate = f'{candidate}_{digest}'
        if candidate in used:
            raise ValueError(f'Cannot create a unique output name for {path.name}')
        used.add(candidate)
        result[path] = candidate
    return result


def save_json(path, value):
    """Atomically replace a completed JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n',
                         encoding='utf-8')
    temporary.replace(path)


def process_directory(input_dir, output_dir, config, generator):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if not input_dir.is_dir():
        raise ValueError(f'Input directory does not exist: {input_dir}')
    files = sorted(path for path in input_dir.glob('*.json') if path.is_file())
    if not files:
        print(f'No JSON trajectories found in {input_dir}')
        return 0, 0, 0
    output_dir.mkdir(parents=True, exist_ok=True)
    names = output_stems(files)
    completed = skipped = failed = 0

    for trajectory_file in files:
        try:
            trajectory = json.loads(trajectory_file.read_text(encoding='utf-8'))
            user_query, events = validate_trajectory(trajectory, trajectory_file.name)
            if not events:
                print(f'Skipped empty trajectory: {trajectory_file.name}')
                skipped += 1
                continue
            windows = split_trajectory(events, config)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            print(f'Failed input {trajectory_file.name}: {exc}')
            failed += 1
            continue

        output_stem = names[trajectory_file]
        expected = {output_dir / f'{output_stem}__{window["window_id"]}.json'
                    for window in windows}
        stale = set(output_dir.glob(f'{output_stem}__window_*.json')) - expected
        if stale:
            print(f'Failed input {trajectory_file.name}: stale output windows exist; '
                  'use a clean output directory')
            failed += 1
            continue

        for window_index, window in enumerate(windows, 1):
            try:
                previous_summary = generator.previous(
                    user_query, window['previous_events'],
                    config['max_previous_summary_tokens'])
                future_summary = generator.future(
                    user_query, window['future_events'],
                    config['max_future_summary_tokens'])
                metadata = {
                    'source_file': trajectory_file.name,
                    'source_path': str(trajectory_file.resolve()),
                    'window_index': window_index,
                    **window['metadata'],
                }
                result = build_window(
                    trajectory_id=trajectory_file.stem,
                    window_id=window['window_id'],
                    user_query=user_query,
                    previous_summary=previous_summary,
                    overlap_events=window['overlap_events'],
                    core_events=window['core_events'],
                    future_summary=future_summary,
                    metadata=metadata,
                )
                destination = output_dir / f'{output_stem}__{window["window_id"]}.json'
                save_json(destination, result)
            except Exception as exc:
                print(f'Failed window {trajectory_file.name}/{window["window_id"]}: {exc}')
                failed += 1
                continue
            completed += 1
            print(f'Saved: {destination}')

    return completed, skipped, failed


def parse_args(argv=None):
    module_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description='Split preprocessed trajectories into summarized windows')
    parser.add_argument('--input-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--config', type=Path, default=module_dir / 'config.yaml')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    module_dir = Path(__file__).resolve().parent
    try:
        load_env(module_dir.parent / '.env')
        config = load_config(args.config)
        generator = SummaryGenerator(
            args.output_dir,
            model=os.environ.get('DEEPSEEK_MODEL') or 'deepseek-flash',
            base_url=os.environ.get('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com',
        )
        completed, skipped, failed = process_directory(
            args.input_dir, args.output_dir, config, generator)
    except (OSError, ValueError) as exc:
        print(f'Configuration error: {exc}')
        return 1
    print(f'Done: {completed} windows, {skipped} empty trajectories, {failed} failures.')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
