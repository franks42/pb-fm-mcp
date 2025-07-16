"""Parser for jq-like path expressions."""
from dataclasses import dataclass
from enum import Enum


class PathComponentType(Enum):
    """Types of path components."""
    KEY = "key"          # Dictionary key access (e.g., .key or ["key"])
    INDEX = "index"      # Array index access (e.g., [0] or [-1])
    WILDCARD = "wildcard"  # Wildcard access (e.g., .* or [*])
    SELECTOR = "selector"  # Filter selector (e.g., [?(@.active==True)])
    SLICE = "slice"      # Array slice access (e.g., [1:3], [2:], [:5])
    FUNCTION = "function"  # jq function calls (e.g., keys, length, type, has(), map())
    OPTIONAL_KEY = "optional_key"  # Optional dictionary key access (e.g., .key?)
    OPTIONAL_INDEX = "optional_index"  # Optional array index access (e.g., [0]?)
    OPTIONAL_WILDCARD = "optional_wildcard"  # Optional wildcard access (e.g., []?)


@dataclass(frozen=False)  # frozen=False allows _replace
class PathComponent:
    """A single component in a path."""
    type: PathComponentType
    value: str | int | slice  # The actual key, index, or slice object
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

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def parse_path(path: str) -> list[PathComponent]:
    """Parse a jq-style path into a list of path components.
    
    Supports:
    - Dot notation (e.g., 'a.b.c')
    - Array indices (e.g., 'a[0].b')
    - Wildcards (e.g., 'a.*.b' or 'a[*].b')
    - Simple selectors (e.g., 'a[?(@.active==true)].b')
    - Pipe operator (|)
    - Literals (e.g., '42', '"hello"', 'true', 'false', 'null')
    """
    if not path:
        return []
    
    logger.debug(f"Parsing path: {path}")
        
    # Handle literal values first
    path_stripped = path.strip()
    
    # Handle numbers
    if path_stripped.replace('.', '').replace('-', '').isdigit():
        if '.' in path_stripped:
            literal_value = float(path_stripped)
        else:
            literal_value = int(path_stripped)
        return [
            PathComponent(
                type=PathComponentType.KEY,
                value=f"LITERAL:{literal_value}",
                raw_value=path_stripped
            )
        ]
    
    # Handle boolean literals
    if path_stripped.lower() in ('true', 'false'):
        literal_value = path_stripped.lower() == 'true'
        return [
            PathComponent(
                type=PathComponentType.KEY,
                value=f"LITERAL:{literal_value}",
                raw_value=path_stripped
            )
        ]
    
    # Handle null literal
    if path_stripped.lower() == 'null':
        return [
            PathComponent(
                type=PathComponentType.KEY,
                value="LITERAL:None",
                raw_value=path_stripped
            )
        ]
    
    # Handle string literals
    if (path_stripped.startswith('"') and path_stripped.endswith('"')) or \
       (path_stripped.startswith("'") and path_stripped.endswith("'")):
        literal_value = path_stripped[1:-1]  # Remove quotes
        return [
            PathComponent(
                type=PathComponentType.KEY,
                value=f"LITERAL:{literal_value}",
                raw_value=path_stripped
            )
        ]
        
    # Handle special cases
    if path == '.[]':
        return [
            PathComponent(
                type=PathComponentType.WILDCARD,
                value='*',
                raw_value='*'
            )
        ]
            
    if path.startswith('{') and path.endswith('}'):  # {a: .a, b: .b}
        # This is an object construction, create a special component
        components = []
        components.append(PathComponent(
            type=PathComponentType.KEY,
            value=f"OBJECT_CONSTRUCT:{path}",
            raw_value=path
        ))
        return components

    # Split by pipe operator
    pipe_parts = path.split('|')
    components = []
    
    logger.debug(f"Pipe parts: {pipe_parts}")
    logger.debug(f"Number of pipe segments: {len(pipe_parts)}")
    
    for part in pipe_parts:
        part = part.strip()
        if not part:
            continue
            
        # Handle array splat
        if part == '[]':
            components.append(PathComponent(
                type=PathComponentType.WILDCARD,
                value='*',
                raw_value='[]'
            ))
            continue
            
        # Handle function calls like select()
        if part.startswith('select(') and part.endswith(')'):
            # Extract the selector expression
            selector_expr = part[7:-1]  # Remove 'select(' and ')'
            logger.debug(f"Function call: select with expression: {selector_expr}")
            components.append(PathComponent(
                type=PathComponentType.SELECTOR,
                value=f"SELECT:{selector_expr}",
                raw_value=part
            ))
            continue
            
        # Handle core jq functions
        jq_functions = ['keys', 'length', 'type']
        if part in jq_functions:
            logger.debug(f"Core jq function: {part}")
            components.append(PathComponent(
                type=PathComponentType.FUNCTION,
                value=part,
                raw_value=part
            ))
            continue
            
        # Handle jq functions with arguments
        if part.startswith('has(') and part.endswith(')'):
            # Extract the argument
            arg = part[4:-1]  # Remove 'has(' and ')'
            logger.debug(f"Function call: has with argument: {arg}")
            components.append(PathComponent(
                type=PathComponentType.FUNCTION,
                value=f"has:{arg}",
                raw_value=part
            ))
            continue
            
        if part.startswith('map(') and part.endswith(')'):
            # Extract the expression
            expr = part[4:-1]  # Remove 'map(' and ')'
            logger.debug(f"Function call: map with expression: {expr}")
            components.append(PathComponent(
                type=PathComponentType.FUNCTION,
                value=f"map:{expr}",
                raw_value=part
            ))
            continue
            
        # Handle object construction
        if part.startswith('{') and part.endswith('}'):
            obj_parts = part[1:-1].split(',')
            logger.debug(f"Object parts: {obj_parts}")
            for obj_part in obj_parts:
                key_expr, value_expr = obj_part.split(':')
                key = key_expr.strip()
                value_path = value_expr.strip()
                logger.debug(f"Object key: {key}, value path: {value_path}")
                components.append(PathComponent(
                    type=PathComponentType.KEY,
                    value=f"{key}:{value_path}",  # Store both key and value path together
                    raw_value=obj_part.strip()
                ))
            continue
            
        # Split by dots
        dot_parts = part.split('.')
        logger.debug(f"Dot parts: {dot_parts}")
        logger.debug(f"Components so far: {components}")
        for dot_part in dot_parts:
            if not dot_part:
                continue
            
            logger.debug(f"Processing dot part: '{dot_part}'")
                
            # Handle bracket expressions
            if '[' in dot_part and ']' in dot_part:
                current = dot_part
                while '[' in current and ']' in current:
                    key_part, bracket_expr = current.split('[', 1)
                    bracket_content, rest = bracket_expr.split(']', 1)
                    
                    # Check for optional selector (? suffix)
                    is_optional = rest.startswith('?')
                    if is_optional:
                        rest = rest[1:]  # Remove the ? from rest
                    
                    if key_part:
                        # Check if key_part is a core jq function
                        if key_part in ['keys', 'length', 'type']:
                            components.append(PathComponent(
                                type=PathComponentType.FUNCTION,
                                value=key_part,
                                raw_value=key_part
                            ))
                        else:
                            components.append(PathComponent(
                                type=PathComponentType.KEY,
                                value=key_part,
                                raw_value=key_part
                            ))
                    
                    if bracket_content.startswith('?(') and bracket_content.endswith(')'):
                        try:
                            selector = _parse_selector(bracket_content)
                            components.append(PathComponent(
                                type=PathComponentType.SELECTOR,
                                value=selector,
                                raw_value=bracket_content
                            ))
                        except ValueError as e:
                            raise ValueError(f"Invalid selector in path: {dot_part}") from e
                    elif bracket_content == '*' or bracket_content == '':
                        # Empty brackets [] are treated as wildcards for array iteration
                        if is_optional:
                            components.append(PathComponent(
                                type=PathComponentType.OPTIONAL_WILDCARD,
                                value='*',
                                raw_value='[]?' if bracket_content == '' else '*?'
                            ))
                        else:
                            components.append(PathComponent(
                                type=PathComponentType.WILDCARD,
                                value='*',
                                raw_value='[]' if bracket_content == '' else '*'
                            ))
                    elif ':' in bracket_content:
                        # Handle slice notation [start:end], [start:], [:end]
                        slice_parts = bracket_content.split(':')
                        if len(slice_parts) == 2:
                            start_str, end_str = slice_parts
                            start = None if start_str.strip() == '' else int(start_str.strip())
                            end = None if end_str.strip() == '' else int(end_str.strip())
                            slice_obj = slice(start, end)
                            components.append(PathComponent(
                                type=PathComponentType.SLICE,
                                value=slice_obj,
                                raw_value=bracket_content
                            ))
                        else:
                            raise ValueError(f"Invalid slice syntax: {bracket_content}")
                    else:
                        try:
                            index = int(bracket_content)
                            if is_optional:
                                components.append(PathComponent(
                                    type=PathComponentType.OPTIONAL_INDEX,
                                    value=index,
                                    raw_value=bracket_content + '?'
                                ))
                            else:
                                components.append(PathComponent(
                                    type=PathComponentType.INDEX,
                                    value=index,
                                    raw_value=bracket_content
                                ))
                        except ValueError:
                            components.append(PathComponent(
                                type=PathComponentType.KEY,
                                value=bracket_content,
                                raw_value=bracket_content
                            ))
                    
                    if rest:
                        components.extend(parse_path(rest))
                        break
                    current = ""  # Clear current to avoid duplicate processing
            else:
                # Handle regular key access only if it's not empty and not already processed
                if dot_part:
                    # Check if it's a wildcard
                    if dot_part == '*':
                        components.append(PathComponent(
                            type=PathComponentType.WILDCARD,
                            value='*',
                            raw_value='*'
                        ))
                    elif dot_part.endswith('?'):
                        # Optional key access
                        key_name = dot_part[:-1]  # Remove the ?
                        components.append(PathComponent(
                            type=PathComponentType.OPTIONAL_KEY,
                            value=key_name,
                            raw_value=dot_part
                        ))
                    elif dot_part in ['keys', 'length', 'type']:
                        # Core jq function that was parsed as a key
                        components.append(PathComponent(
                            type=PathComponentType.FUNCTION,
                            value=dot_part,
                            raw_value=dot_part
                        ))
                    else:
                        components.append(PathComponent(
                            type=PathComponentType.KEY,
                            value=dot_part,
                            raw_value=dot_part
                        ))
    
    return components
