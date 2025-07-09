# base64expand.py
# Utility for recursively expanding base64-encoded strings in JSON-like structures.

import json
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from hastra_types import JSONType

def is_base64(s: str) -> bool:
    # Heuristic: base64 strings are usually longer than 8 chars, only contain base64 chars, and length is a multiple of 4 (with or without padding)
    import re
    s = s.strip()
    if len(s) < 8:
        return False
    if not re.fullmatch(r'[A-Za-z0-9+/=_-]+', s):
        return False
    # Try to decode
    try:
        import base64
        base64.b64decode(s + '=' * (-len(s) % 4))
        return True
    except Exception:
        return False

def base64expand(obj: 'JSONType') -> 'JSONType':
    """
    Recursively expand all base64-encoded strings in a JSON-like structure.
    If a base64 string decodes to utf-8, and that string is JSON or base64, recursively expand.
    If not utf-8, leave as original base64 string.
    
    Returns:
        - Decoded and expanded value for dict, list, or str (including base64-encoded JSON, numbers, or further base64).
        - For unexpected types (e.g., int, float, bool, None), returns the value unchanged.
    """
    if isinstance(obj, dict):
        # Recursively expand all values in the dict
        return {k: base64expand(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Recursively expand all items in the list
        return [base64expand(v) for v in obj]
    elif isinstance(obj, str):
        s = obj
        if is_base64(s):
            try:
                import base64
                b = base64.b64decode(s + '=' * (-len(s) % 4))
            except Exception:
                return s
            try:
                s2 = b.decode('utf-8')
            except Exception:
                return s  # binary, not utf-8
            # Try JSON
            try:
                j = json.loads(s2)
                # Recursively expand the decoded JSON
                return base64expand(j)
            except Exception:
                pass
            # Try base64 again
            if is_base64(s2):
                return base64expand(s2)
            # Recursively expand the decoded string (in case it's a base64 blob inside a string)
            return base64expand(s2)
        else:
            return s
    else:
        # For int, float, bool, None, or any other type, return as-is
        return obj

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Recursively expand all base64-encoded strings in a JSON-like structure from stdin or file.")
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help='Input JSON file (default: stdin)')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help='Output file (default: stdout)')
    parser.add_argument('--indent', type=int, default=2, help='Indentation for output JSON (default: 2)')
    args = parser.parse_args()

    data = json.load(args.input)
    expanded = base64expand(data)
    json.dump(expanded, args.output, indent=args.indent, ensure_ascii=False)
    args.output.write('\n')
