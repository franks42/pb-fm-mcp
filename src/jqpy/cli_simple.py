#!/usr/bin/env python3
"""
Simple jqpy CLI that matches jq behavior exactly.
"""

import argparse
import json
import sys
from typing import Any

from . import get_path


def main():
    """Main entry point for jqpy CLI."""
    parser = argparse.ArgumentParser(description='jqpy - jq-like JSON processor')
    parser.add_argument('filter', nargs='?', default='.',
                       help='jq filter expression')
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'),
                       help='Input file (default: stdin)')
    parser.add_argument('--argfile', type=str, help=argparse.SUPPRESS)
    parser.add_argument('-c', '--compact-output', action='store_true',
                       help='compact output')
    parser.add_argument('-r', '--raw-output', action='store_true',
                       help='raw output')
    parser.add_argument('-s', '--slurp', action='store_true',
                       help='slurp inputs into array')
    parser.add_argument('-n', '--null-input', action='store_true',
                       help='use null input')
    parser.add_argument('-e', '--exit-status', action='store_true',
                       help='set exit status based on output')
    
    args = parser.parse_args()
    
    # Handle input
    if args.null_input:
        data = None
    elif args.argfile:
        with open(args.argfile, 'r') as f:
            content = f.read().strip()
            if args.slurp:
                # Split by lines and parse each as JSON
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                data = [json.loads(line) for line in lines]
            else:
                data = json.loads(content) if content else None
    elif args.file:
        content = args.file.read().strip()
        if args.slurp:
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            data = [json.loads(line) for line in lines]
        else:
            data = json.loads(content) if content else None
    else:
        if not sys.stdin.isatty():
            content = sys.stdin.read().strip()
            if args.slurp:
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                data = [json.loads(line) for line in lines]
            else:
                data = json.loads(content) if content else None
        else:
            data = None
    
    # Process with jqpy
    try:
        results = list(get_path(data, args.filter))
    except Exception as e:
        print(f"jqpy: error: {e}", file=sys.stderr)
        return 2
    
    # Handle exit status
    if args.exit_status:
        if not results:
            return 1
        # Check if any result is falsy (false, null, 0, "", [])
        for result in results:
            if result is False:
                return 1
    
    # Output results - each on separate line like jq
    for result in results:
        if args.raw_output:
            if isinstance(result, str):
                print(result)
            else:
                print(str(result))
        else:
            if args.compact_output:
                print(json.dumps(result, separators=(',', ':')))
            else:
                # Use pretty printing by default (like jq)
                print(json.dumps(result, indent=2))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())