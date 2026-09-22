"""Batch preprocess trajectory/*/agent/trajectory.json from this repository."""
import os
import re
from datetime import datetime
from pathlib import Path

from src.preprocess import Client, load, normalize, save


ROOT = Path(__file__).resolve().parent


def load_env(path):
    """Load src/.env without overwriting existing environment variables."""
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
            raise ValueError(f'{path.name}:{number}: expected KEY=VALUE')
        if value.startswith(('"', "'")):
            quote = value[0]
            end = value.find(quote, 1)
            if end < 0 or (value[end + 1:].strip() and not value[end + 1:].strip().startswith('#')):
                raise ValueError(f'{path.name}:{number}: invalid quoted value')
            value = value[1:end]
        else:
            value = re.split(r'\s+#', value, maxsplit=1)[0].rstrip()
        os.environ.setdefault(key, value)


def create_run_directory(runs_root):
    """Reserve today's next sequence number without overwriting an old run."""
    runs_root.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime('%m-%d')
    prefix = date + '_'
    numbers = [int(path.name[len(prefix):]) for path in runs_root.iterdir()
               if path.name.startswith(prefix) and path.name[len(prefix):].isdigit()]
    sequence = max(numbers, default=0) + 1
    while True:
        directory = runs_root / f'{date}_{sequence}'
        try:
            directory.mkdir()
            return directory
        except FileExistsError:
            sequence += 1


def main():
    try:
        load_env(ROOT / 'src' / '.env')
    except (OSError, ValueError) as error:
        print(f'Configuration error: {error}')
        return 1

    inputs = sorted((ROOT / 'trajectory').glob('*/agent/trajectory.json'))
    inputs = [path for path in inputs if path.is_file()]
    if not inputs:
        print('No inputs found: trajectory/*/agent/trajectory.json')
        return 1
    if not os.environ.get('DEEPSEEK_API_KEY', '').strip():
        print('Set DEEPSEEK_API_KEY in src/.env or the environment before running.')
        return 1

    run_directory = create_run_directory(ROOT / 'runs')
    processed = run_directory / 'processed_trajectory'
    processed.mkdir()
    model = os.environ.get('DEEPSEEK_MODEL') or 'deepseek-flash'
    base_url = os.environ.get('DEEPSEEK_BASE_URL') or 'https://api.deepseek.com'
    client = Client(run_directory, model=model, base_url=base_url)
    summary = {'total': len(inputs), 'succeeded': 0, 'failed': 0, 'cases': []}
    print(f'Run directory: {run_directory}')

    for index, input_path in enumerate(inputs, 1):
        case_name = input_path.parent.parent.name
        source_trajectory = input_path.relative_to(ROOT).as_posix()
        destination = processed / f'trajectory{index}.json'
        record = {'case': case_name, 'input': source_trajectory}
        print(f'[{index}/{len(inputs)}] {case_name}')
        try:
            trace, source = load(input_path)
            result = normalize(trace, source, client)
            result['metadata'] = {'source_trajectory': source_trajectory}
            save(destination, result)
        except Exception as error:
            # Keep processing the other cases; exclude credentials from diagnostics.
            detail = client.redactor.hide(str(error))
            record.update(status='failed', error=detail)
            summary['failed'] += 1
            print(f'Failed: {detail}')
        else:
            record.update(status='succeeded', output=destination.relative_to(run_directory).as_posix())
            summary['succeeded'] += 1
        summary['cases'].append(record)
        save(run_directory / 'summary.json', summary)

    print(f'Done: {summary["succeeded"]} succeeded, {summary["failed"]} failed.')
    print(f'Results: {processed}')
    return 1 if summary['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
