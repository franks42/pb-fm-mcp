#!/usr/bin/env python3
"""
jqpy - A jq-like command-line JSON processor using Python

This module provides a command-line interface similar to jq but using Python's
syntax for path expressions and selectors.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any, TextIO

from . import get_path, parse_path
from .parser import PathComponent


class JQPYError(Exception):
    """Base exception for jqpy errors."""
    pass

def load_json(input_file: TextIO | None = None, null_input: bool = False) -> Any:
    """Load JSON from file or stdin."""
    if null_input:
        return None
        
    try:
        if input_file is None or input_file == sys.stdin:
            if sys.stdin.isatty():
                # No input and not a pipe/file redirection
                return {}
            data = sys.stdin.read().strip()
            if not data:
                return {}
            return json.loads(data)
        else:
            # Handle file input
            if hasattr(input_file, 'read'):
                # Already an open file
                content = input_file.read().strip()
                return json.loads(content) if content else {}
            else:
                # Path-like object or string
                with open(str(input_file), encoding='utf-8') as f:
                    content = f.read().strip()
                    return json.loads(content) if content else {}
    except json.JSONDecodeError as e:
        raise JQPYError(f"parse error: {e} at line {e.lineno} column {e.colno} (char {e.pos})")
    except FileNotFoundError as e:
        raise JQPYError(f"jqpy: {e.filename}: No such file or directory")

def format_output(
    result: Any, 
    compact: bool = False, 
    join_output: bool = False,
    indent: int | None = None,
    tab: bool = False,
    raw_output: bool = False
) -> str:
    """Format the output based on the result type and options."""
    if result is None:
        return "null"
    
    # Handle string results
    if isinstance(result, str):
        # If raw output is requested, return the string as-is
        if raw_output:
            return result
        # Otherwise, return as a JSON-encoded string
        return json.dumps(result)
    
    # Handle boolean results
    if isinstance(result, bool):
        return "true" if result else "false"
    
    # Handle numeric results
    if isinstance(result, (int, float)):
        # If raw output is requested, return the number as a string
        if raw_output:
            return str(result)
        # Otherwise, return as a JSON-encoded number
        return json.dumps(result)
    
    # Handle lists
    if isinstance(result, list):
        # For empty list, return []
        if not result:
            return "[]"
            
        # If raw output is requested and it's a list of strings/numbers, join with newlines
        if raw_output and all(isinstance(x, (str, int, float, bool)) for x in result):
            return "\n".join(str(x) for x in result)
            
        # Handle list of values
        if tab:
            return json.dumps(result, indent='\t', ensure_ascii=False)
        return json.dumps(
            result, 
            indent=None if compact else (indent or 2), 
            ensure_ascii=False,
            separators=(',', ':') if compact else None
        )
    
    # Handle dictionaries
    if isinstance(result, dict):
        if tab:
            return json.dumps(result, indent='\t', ensure_ascii=False)
        return json.dumps(
            result, 
            indent=None if compact else (indent or 2), 
            ensure_ascii=False,
            separators=(',', ':') if compact else None
        )
    
    # For any other type, convert to string and handle raw output
    str_result = str(result)
    return str_result if raw_output else json.dumps(str_result)

def process_path_expression(path_expr: str) -> list[PathComponent]:
    """Process a path expression into path components."""
    try:
        return parse_path(path_expr)
    except Exception as e:
        raise JQPYError(f"jq: error: {e!s}")

def process_input_streaming(
    data: Any,
    path_expr: str = ".",
    default: str | None = None,
    raw_output: bool = False,
    compact: bool = False,
    join_output: bool = False,
    join_string: str | None = None,
    exit_status: bool = False,
    tab: bool = False,
    slurp: bool = False,
    args: argparse.Namespace | None = None
):
    """Process input data with the given path expression and yield individual results."""
    try:
        # Handle empty input
        if data is None:
            if default is not None:
                yield default
                return
            if not exit_status:
                return
            raise JQPYError("No input provided")

        # Handle root selector
        if path_expr == "." and not slurp:
            yield data
            return
        
        try:
            path_components = process_path_expression(path_expr)
            # Use iterator directly - no list conversion!
            results_iterator = get_path(data, path_components, only_first_path_match=False)
            
            has_results = False
            for result in results_iterator:
                has_results = True
                yield result
            
            # Handle empty results
            if not has_results:
                if default is not None:
                    yield default
                elif exit_status:
                    raise JQPYError("No results found")
                    
        except Exception as e:
            if exit_status:
                raise JQPYError(f"jq: error: {e!s}")
            raise JQPYError(f"jq: error: {e!s}")

    except JQPYError:
        if exit_status:
            raise
        raise
    except Exception as e:
        if exit_status:
            raise JQPYError(f"jq: error: {e!s}")
        raise JQPYError(f"jq: error: {e!s}")


def process_input(
    data: Any,
    path_expr: str = ".",
    default: str | None = None,
    raw_output: bool = False,
    compact: bool = False,
    join_output: bool = False,
    join_string: str | None = None,
    exit_status: bool = False,
    tab: bool = False,
    slurp: bool = False,
    args: argparse.Namespace | None = None
) -> tuple[Any, bool]:
    """Process input data with the given path expression."""
    # Use streaming version internally
    results, success = process_input_streaming(
        data, path_expr, default, raw_output, compact, join_output,
        join_string, exit_status, tab, slurp, args
    )
    
    if not success:
        return None, False
    
    if not results:
        return None, success
    
    # For legacy compatibility, return array format
    return results[0] if len(results) == 1 else results, success

def parse_arguments(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='jqpy - Command-line JSON processor',
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  $ echo '{"foo": 0}' | jqpy .
  {
    "foo": 0
  }
  $ echo '{"foo": 0, "bar": 1}' | jqpy .
  {
    "foo": 0,
    "bar": 1
  }
  $ echo '{"user":"steve","titles":["JQ Fan","RFC 8259"]}' | jqpy .user
  "steve"
  $ echo '{"user":"steve","titles":["JQ Fan","RFC 8259"]}' | jqpy -r .user
  steve
  $ echo '{"user":"steve","titles":["JQ Fan","RFC 8259"]}' | jqpy -r '.titles | join(", ")'
  JQ Fan, RFC 8259
"""
    )
    
    # Mimic jq's argument parsing
    parser.add_argument('filter', nargs='?', default='.',
                      help='jq filter (default: .)')
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'),
                      help='Input file (default: stdin)')
    
    # Add --argfile option for compatibility with our test runner
    parser.add_argument('--argfile', type=str, help=argparse.SUPPRESS)
    
    # Output options
    output_group = parser.add_argument_group('Output options')
    output_group.add_argument('-c', '--compact-output', action='store_true',
                           help='compact instead of pretty-printed output')
    output_group.add_argument('-r', '--raw-output', action='store_true',
                           help='output raw strings, not JSON texts')
    output_group.add_argument('-j', '--join-output', action='store_true',
                           help='like -r but jq won\'t print newlines')
    output_group.add_argument('--tab', action='store_true',
                           help='use tabs for indentation')
    output_group.add_argument('--indent', type=int, default=2,
                           help='use given number of spaces for indentation')
    
    # Input options
    input_group = parser.add_argument_group('Input options')
    input_group.add_argument('-s', '--slurp', action='store_true',
                          help='read (slurp) all inputs into an array')
    input_group.add_argument('-n', '--null-input', action='store_true',
                          help='use null as input value')
    
    # Program options
    prog_group = parser.add_argument_group('Program options')
    prog_group.add_argument('-e', '--exit-status', action='store_true',
                          help='set exit status based on output')
    prog_group.add_argument('--seq', action='store_true',
                          help='use application/json-seq ASCII RS/LF for output')
    prog_group.add_argument('--stream', action='store_true',
                          help='parse input in streaming fashion')
    
    # Other options
    other_group = parser.add_argument_group('Other options')
    other_group.add_argument('-C', '--color-output', action='store_true',
                          help='colorize output (currently not supported)')
    other_group.add_argument('-M', '--monochrome-output', action='store_true',
                          help='produce monochrome output')
    other_group.add_argument('-S', '--sort-keys', action='store_true',
                          help='sort object keys (not implemented)')
    other_group.add_argument('--help', action='help',
                          help='show this help message and exit')
    other_group.add_argument('--version', action='version',
                          version='jqpy 0.1.0')
    
    return parser.parse_args(args)

def main(args: Sequence[str] | None = None) -> int:
    """Main entry point for the jqpy command-line tool."""
    try:
        parsed_args = parse_arguments(args)
        
        # Handle input
        input_file = None
        try:
            # Use --argfile if provided, otherwise use the positional file argument
            if hasattr(parsed_args, 'argfile') and parsed_args.argfile:
                input_file = open(parsed_args.argfile)
            elif parsed_args.file is None and not parsed_args.null_input:
                # If no file is provided and not using null input, default to stdin
                input_file = sys.stdin
            
            data = load_json(input_file, parsed_args.null_input)
        except JQPYError as e:
            print(str(e), file=sys.stderr)
            return 2
        finally:
            # Close the file if we opened it (for --argfile)
            if input_file and input_file != sys.stdin:
                input_file.close()
        
        # Process input using streaming
        try:
            has_output = False
            for result in process_input_streaming(
                data,
                parsed_args.filter,
                raw_output=parsed_args.raw_output,
                compact=parsed_args.compact_output,
                join_output=parsed_args.join_output,
                tab=parsed_args.tab,
                exit_status=parsed_args.exit_status,
                slurp=parsed_args.slurp,
                args=parsed_args
            ):
                has_output = True
                # Format and output each result individually
                output = format_output(
                    result,
                    compact=parsed_args.compact_output,
                    join_output=parsed_args.join_output,
                    indent=0 if parsed_args.compact_output else parsed_args.indent,
                    tab=parsed_args.tab,
                    raw_output=parsed_args.raw_output
                )
                if output is not None:
                    print(output, end='' if parsed_args.join_output else '\n')
            
            # If exit_status is True and no output, return 1 for failure
            if parsed_args.exit_status and not has_output:
                return 1
            return 0
            
        except JQPYError as e:
            print(str(e), file=sys.stderr)
            return 2
            
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print(f"jqpy: error: {e}", file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
