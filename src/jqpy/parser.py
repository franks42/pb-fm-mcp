"""Parser for jq-like path expressions."""
from enum import Enum
from dataclasses import dataclass
from typing import List, Union, Optional


class PathComponentType(Enum):
    """Types of path components."""
    KEY = "key"          # Dictionary key access (e.g., .key or ["key"])
    INDEX = "index"      # Array index access (e.g., [0] or [-1])
    WILDCARD = "wildcard"  # Wildcard access (e.g., .* or [*])
    SELECTOR = "selector"  # Filter selector (e.g., [?(@.active==True)])


@dataclass(frozen=False)  # frozen=False allows _replace
class PathComponent:
    """A single component in a path."""
    type: PathComponentType
    value: Union[str, int]  # The actual key or index
    raw_value: str  # Original string representation


def _parse_selector(selector: str) -> dict:
    """Parse a selector expression into a filter condition.
    
    Supports:
    - Equality checks: @.key==value
    - Numeric comparisons: @.key>value, @.key<value, @.key>=value, @.key<=value
    """
    if not (selector.startswith('?(') and selector.endswith(')')):
        raise ValueError(f"Invalid selector format: {selector}")
    
    expr = selector[2:-1]  # Remove ?( and )
    
    # Check for comparison operators
    operators = ['==', '>=', '<=', '>', '<']
    op = None
    for op_test in operators:
        if op_test in expr:
            op = op_test
            break
    
    if op:
        left, right = expr.split(op, 1)
        left = left.strip()
        right = right.strip()
        
        # Handle @.key format
        if left.startswith('@.'):
            key = left[2:]
            # Remove quotes if present
            if (right.startswith('"') and right.endswith('"')) or \
               (right.startswith("'") and right.endswith("'")):
                right = right[1:-1]
            # Convert to boolean if needed
            elif right.lower() == 'true':
                right = True
            elif right.lower() == 'false':
                right = False
            # Convert to number if possible
            elif right.replace('.', '').isdigit() or \
                 (right.startswith('-') and right[1:].replace('.', '').isdigit()):
                if '.' in right:
                    right = float(right)
                else:
                    right = int(right)
            
            return {'type': 'compare', 'key': key, 'op': op, 'value': right}
    
    raise ValueError(f"Unsupported selector expression: {expr}")

def parse_path(path: str) -> List[PathComponent]:
    """Parse a jq-style path into a list of path components.
    
    Supports:
    - Dot notation (e.g., 'a.b.c')
    - Array indices (e.g., 'a[0].b')
    - Wildcards (e.g., 'a.*.b' or 'a[*].b')
    - Simple selectors (e.g., 'a[?(@.active==true)].b')
    """
    if not path:
        return []
        
    components = []
    
    # First, handle the special case of a wildcard with a selector
    if '.*[?(@' in path or '[*][?(@' in path:
        # Split into parts before and after the wildcard+selector
        if '.*[?(@' in path:
            before, after = path.split('.*[?(@', 1)
            wildcard = '*'
        else:
            before, after = path.split('[*][?(@', 1)
            wildcard = '*'
            
        # Parse the part before the wildcard+selector
        if before:
            components.extend(parse_path(before))
            
        # Add the wildcard
        components.append(PathComponent(
            type=PathComponentType.WILDCARD,
            value=wildcard,
            raw_value=wildcard
        ))
        
        # Parse the selector part
        selector_end = after.find(')') + 1
        if selector_end > 0:
            selector = f"?(@{after[:selector_end]}"
            try:
                selector_obj = _parse_selector(selector)
                components.append(PathComponent(
                    type=PathComponentType.SELECTOR,
                    value=selector_obj,
                    raw_value=selector
                ))
            except ValueError as e:
                raise ValueError(f"Invalid selector in path: {path}") from e
            
            # Parse any remaining path after the selector
            remaining_path = after[selector_end:].lstrip(']')
            if remaining_path.startswith('.'):
                components.extend(parse_path(remaining_path[1:]))
            
            return components
    
    # Handle each part of the path (split by dots)
    for part in path.split('.'):
        if not part:
            continue  # Skip empty parts from leading/trailing/multiple dots
            
        # Handle array access, wildcard, or selector in brackets: a[0], a[*], a[?(@.active)]
        if '[' in part and ']' in part:
            # Handle regular bracket expressions
            current_part = part
            while '[' in current_part and ']' in current_part:
                key_part, bracket_expr = current_part.split('[', 1)
                bracket_content, rest = bracket_expr.split(']', 1)
            
                # Add the key part if it exists (e.g., 'items' in 'items[0]')
                if key_part:
                    components.append(PathComponent(
                        type=PathComponentType.KEY,
                        value=key_part,
                        raw_value=key_part
                    ))
                
                # Handle the content inside brackets
                if bracket_content.startswith('?(') and bracket_content.endswith(')'):  # Selector
                    try:
                        selector = _parse_selector(bracket_content)
                        components.append(PathComponent(
                            type=PathComponentType.SELECTOR,
                            value=selector,
                            raw_value=bracket_content
                        ))
                        continue  # Skip the rest of the processing for this bracket
                    except ValueError as e:
                        raise ValueError(f"Invalid selector in path: {part}") from e
                elif bracket_content == '*':  # Wildcard
                    components.append(PathComponent(
                        type=PathComponentType.WILDCARD,
                        value='*',
                        raw_value='*'
                    ))
                else:  # Index or key
                    try:
                        # Try to parse as an integer index
                        index = int(bracket_content)
                        components.append(PathComponent(
                            type=PathComponentType.INDEX,
                            value=index,
                            raw_value=bracket_content
                        ))
                    except ValueError:
                        # If not an integer, treat as a key
                        components.append(PathComponent(
                            type=PathComponentType.KEY,
                            value=bracket_content,
                            raw_value=bracket_content
                        ))
                
                current_part = rest
            
            # Add any remaining part after all brackets
            if current_part:
                components.append(PathComponent(
                    type=PathComponentType.KEY,
                    value=current_part,
                    raw_value=current_part
                ))
        else:
            # Handle dot notation wildcard (e.g., 'a.*.b')
            if part == '*':
                components.append(PathComponent(
                    type=PathComponentType.WILDCARD,
                    value='*',
                    raw_value='*'
                ))
            else:
                # Regular key
                components.append(PathComponent(
                    type=PathComponentType.KEY,
                    value=part,
                    raw_value=part
                ))
    
    return components
