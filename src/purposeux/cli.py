"""Local command interface; user-owned screenshots never leave the machine."""
import argparse
import json
from pathlib import Path
import sys

from . import __version__


def main():
    parser = argparse.ArgumentParser(prog='purposeux')
    parser.add_argument('--version', action='version', version=__version__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor')
    training = commands.add_parser('train')
    training.add_argument('--data', default='data/train.jsonl')
    training.add_argument('--output', default='artifacts/local')
    training.add_argument('--iters', type=int, default=64)
    training.add_argument('--learning-rate', type=float, default=0.0001)
    training.add_argument('--seed', type=int, default=17)
    for name in ('judge', 'evaluate'):
        command = commands.add_parser(name)
        command.add_argument('--data', required=True, help='Local JSONL records; judge also accepts a single record JSON')
        command.add_argument('--adapter')
        if name == 'judge':
            command.add_argument('--index', type=int, default=0)
        else:
            command.add_argument('--output', required=True)
            command.add_argument('--limit', type=int)
            command.add_argument('--ablate', action='store_true', help='Also score a blank image to measure image sensitivity')
    args = parser.parse_args()
    try:
        from .model import environment, evaluate, open_model, score, train
        from .contracts import read_records
        if args.command == 'doctor':
            result = environment()
            if not result['metal_available']:
                raise ValueError('This release requires an Apple Silicon Metal device')
        elif args.command == 'train':
            result = train(args.data, args.output, args.iters, args.learning_rate, args.seed)
        elif args.command == 'judge':
            rows = read_records(args.data)
            if not 0 <= args.index < len(rows):
                raise ValueError('index is outside the input records')
            model, processor = open_model(args.adapter)
            result = score(model, processor, rows[args.index])
            result.update(environment(), adapter=bool(args.adapter))
        else:
            if args.limit is not None and args.limit < 1:
                raise ValueError('limit must be positive')
            result = evaluate(args.data, args.adapter, args.limit, args.ablate)
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, RuntimeError, json.JSONDecodeError) as error:
        print(f'purposeux: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
