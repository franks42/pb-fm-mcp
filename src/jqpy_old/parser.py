"""
Path expression parser for jqpy.

This module provides functionality to parse jq-style path expressions into
structured path components that can be used to traverse nested data structures.
"""

from enum import Enum, auto
from typing import NamedTuple


class PathComponentType(Enum):
    """Types of path components."""
    KEY = auto()
    INDEX = auto()
    SELECT_ALL = auto()
    # Future: Add more types like SLICE, FILTER, etc.


class PathComponent(NamedTuple):
    """A single component in a path expression."""
    type: PathComponentType
    value: str | int | None
    raw_value: str | None = None  # Store the original string representation for keys

    def __str__(self) -> str:
        if self.type == PathComponentType.KEY:
            return str(self.raw_value if self.raw_value is not None else self.value)
        elif self.type == PathComponentType.INDEX:
            return f"[{self.value}]"
        elif self.type == PathComponentType.SELECT_ALL:
            return "[]"
        return ""


def parse_path(path: str) -> list[PathComponent]:
    """
    Parse a jq-style path expression into a list of path components.

    Args:
        path: The path string to parse (e.g., "a.b[0]")

    Returns:
        A list of PathComponent objects representing the parsed path.

    Raises:
        ValueError: If the path string is malformed.
    """
    if not path:
        return []

    components: list[PathComponent] = []
    i = 0
    n = len(path)
    
    while i < n:
        # Skip any leading whitespace
        while i < n and path[i].isspace():
            i += 1
            
        if i >= n:
            break
            
        # Handle bracket notation: ["key"] or [0] or []
        if path[i] == '[':
            i += 1  # Skip '['
            
            # Skip whitespace after '['
            while i < n and path[i].isspace():
                i += 1
                
            if i >= n:
                raise ValueError("Unterminated bracket")
                
            # Handle empty brackets []
            if path[i] == ']':
                components.append(PathComponent(PathComponentType.SELECT_ALL, None))
                i += 1  # Skip ']'
                continue
                
            # Check if it's a string or a number
            if path[i] == '"' or path[i] == "'":
                # String key in brackets
                quote = path[i]
                i += 1  # Skip opening quote
                start = i
                while i < n and path[i] != quote:
                    if path[i] == '\\' and i + 1 < n:
                        i += 1  # Skip escaped character
                    i += 1
                    
                if i >= n:
                    raise ValueError("Unterminated string in path")
                    
                key = path[start:i].replace(f'\\{quote}', quote)
                # For quoted keys in brackets, raw_value should include the quotes
                raw_key = path[start-1:i+1]
                components.append(PathComponent(PathComponentType.KEY, key, raw_key))
                i += 1  # Skip closing quote
            else:
                # Number index
                start = i
                is_negative = False
                
                # Handle negative index
                if path[i] == '-':
                    is_negative = True
                    i += 1
                    start = i  # Update start to the first digit
                    if i >= n or not path[i].isdigit():
                        raise ValueError("Invalid index after '-'")
                
                # Parse digits
                while i < n and path[i].isdigit():
                    i += 1
                    
                if i == start or (is_negative and i == start):
                    raise ValueError("Expected number inside brackets")
                    
                index_str = path[start:i]
                if is_negative:
                    index = -int(index_str)
                    raw_value = f'-{index_str}'
                else:
                    index = int(index_str)
                    raw_value = index_str
                components.append(PathComponent(PathComponentType.INDEX, index, raw_value))
                
            # Skip whitespace before ']'
            while i < n and path[i].isspace():
                i += 1
                
            if i >= n or path[i] != ']':
                raise ValueError("Expected ']' after index")
                
            i += 1  # Skip ']'
            
        # Handle dot notation
        elif path[i] == '.':
            i += 1  # Skip '.'
            
            # Skip whitespace after '.'
            while i < n and path[i].isspace():
                i += 1
                
            print(f"Handling dot notation at position {i}")
                
            if i >= n:
                raise ValueError("Path ends with dot")
                
            # Handle quoted key after dot
            if path[i] == '"' or path[i] == "'":
                quote = path[i]
                i += 1  # Skip opening quote
                start = i
                while i < n and path[i] != quote:
                    if path[i] == '\\' and i + 1 < n:
                        i += 1  # Skip escaped character
                    i += 1
                    
                if i >= n:
                    raise ValueError("Unterminated string in path")
                    
                key = path[start:i].replace(f'\\{quote}', quote)
                # For quoted keys, raw_value should include the quotes
                raw_key = path[start-1:i+1]
                components.append(PathComponent(PathComponentType.KEY, key, raw_key))
                i += 1  # Skip closing quote
            else:
                # Simple key (letters, numbers, underscores)
                start = i
                while i < n and (path[i].isalnum() or path[i] == '_' or path[i] == '\\'):
                    i += 1
                    
                if i == start:
                    raise ValueError("Expected identifier after dot")
                    
                key = path[start:i]
                # Unescape the key (remove backslashes before dots and brackets)
                unescaped_key = key.replace('\\.', '.').replace('\\[', '[').replace('\\]', ']')
                components.append(PathComponent(PathComponentType.KEY, unescaped_key, key))
                
        # Handle top-level key (first component without leading dot)
        elif not components and (path[i].isalpha() or path[i] == '_' or path[i] == '\\'):
            start = i
            i += 1
            
            # Buffer to build the key with unescaped characters
            key_parts = []
            
            while i <= n:
                if i >= n:
                    # End of string
                    key_parts.append(path[start:i])
                    break
                    
                if path[i] == '\\':
                    # Add the part before the backslash
                    if start < i:
                        key_parts.append(path[start:i])
                    
                    # Skip the backslash and add the next character literally
                    i += 1
                    if i < n:
                        key_parts.append(path[i])
                        i += 1
                    start = i
                elif path[i] == '.' or path[i] == '[' or path[i] == ']' or path[i].isspace():
                    # End of key
                    if start < i:
                        key_parts.append(path[start:i])
                    break
                else:
                    i += 1
            
            # Join all parts to form the final key
            key = ''.join(key_parts)
            # For unquoted keys, the raw_value is the same as the key
            components.append(PathComponent(PathComponentType.KEY, key, key))
            
        else:
            raise ValueError(f"Unexpected character '{path[i]}' at position {i}")
    
    return components


# For testing
if __name__ == "__main__":
    # Simple test
    path = "a.b.c"
    print(f"Parsing path: {path}")
    for comp in parse_path(path):
        print(f"- {comp.type.name}: {comp.value}")
