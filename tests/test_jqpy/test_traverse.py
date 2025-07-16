import pytest
from src.jqpy import get_path, PathComponent, PathComponentType

# TODO: Uncomment these tests once array splat and depth functionality is implemented
# def test_traverse_depth():
#     """Test traversal with depth logging."""
#     data = {'a': {'b': {'c': 1}}}
#     components = [
#         PathComponent(type=PathComponentType.KEY, value='a', raw_value='a'),
#         PathComponent(type=PathComponentType.KEY, value='b', raw_value='b'),
#         PathComponent(type=PathComponentType.KEY, value='c', raw_value='c')
#     ]
#     
#     # Test with default depth
#     results = list(get_path(data, components))
#     assert len(results) == 1
#     assert results[0] == 1

#     # Test with max depth
#     results = list(get_path(data, components, max_depth=2))
#     assert len(results) == 0  # Should be empty since we hit max depth

# def test_array_splat_with_object():
#     """Test array splat followed by object construction."""
#     data = [{'a': 1}, {'b': 2}]
#     components = [
#         PathComponent(type=PathComponentType.KEY, value='[]', raw_value='.[]'),
#         PathComponent(type=PathComponentType.KEY, value='key:.key', raw_value='key: .key'),
#         PathComponent(type=PathComponentType.KEY, value='value:.value', raw_value='value: .value')
#     ]
#     
#     # Test with default depth
#     results = list(get_path(data, components))
#     assert len(results) == 2
#     assert {'key': 'a', 'value': 1} in results
#     assert {'key': 'b', 'value': 2} in results

#     # Test with max depth
#     results = list(get_path(data, components, max_depth=2))
#     assert len(results) == 0  # Should be empty since we hit max depth
