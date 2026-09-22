"""Run with python -m src.preprocess from the repository root."""
import argparse
import os
from pathlib import Path

from . import Client, load, normalize, save


def main(argv=None):
    parser = argparse.ArgumentParser(description='Normalize Terminal-Bench 2.0 ATIF-v1.7 trajectories')
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='Output directory')
    parser.add_argument('--model', default=os.environ.get('DEEPSEEK_MODEL', 'deepseek-flash'))
    parser.add_argument('--base-url', default=os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'))
    parser.add_argument('--resume', action='store_true', help='Reuse validated response cache')
    args = parser.parse_args(argv)
    trace, source = load(args.input)
    client = Client(args.output, model=args.model, base_url=args.base_url, resume=args.resume)
    result = normalize(trace, source, client)
    destination = args.output / 'normalized_trace.json'
    save(destination, result)
    print(f'Saved: {destination}')


if __name__ == '__main__':
    main()
