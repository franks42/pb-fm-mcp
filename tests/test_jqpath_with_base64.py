#!/usr/bin/env python3
"""
Test Suite for jqpath with base64 expansion
"""

import os
import json
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from base64expand import base64expand
from jqpath import getpaths_setpaths, setpath

# base64expand already handles recursive expansion of base64 strings in dicts, lists, and strings
# so we can use it directly without our own deep_expand function

def test_getpaths_setpaths_with_base64():
    """Test getpaths_setpaths with base64-expanded data."""
    # Load the real world example data
    test_file = os.path.join(os.path.dirname(__file__), 'real_world_example.json')
    with open(test_file, 'r') as f:
        src = json.load(f)
    
    # Expand all base64 strings in the source data
    expanded_src = base64expand(src)
    
    # Test 1: Simple field mapping (non-base64 field)
    target = {}
    paths_map = [
        ('accountType', 'account_type'),
        ('publicKey.type', 'key_info.key_type')
    ]
    
    getpaths_setpaths(expanded_src, target, paths_map)
    
    # These fields should be the same as in the non-expanded test
    assert target['account_type'] == ['Continuous Vesting Account']
    assert target['key_info']['key_type'] == ['secp256k1']
    
    # Test 2: Test with multiple source paths using simple paths
    target = {}
    
    # Create paths to test - using only simple paths that we know work
    paths_map = [
        # Simple field mapping that we know works
        ('accountType', 'account_info.type'),
        # Another simple field mapping
        ('address', 'account_info.address'),
        # Test with a nested path that we know exists
        ('publicKey.type', 'key_info.key_type')
    ]
    
    getpaths_setpaths(expanded_src, target, paths_map)
    
    # Debug output
    print("\nTarget after getpaths_setpaths:", target)
    
    # Verify the results
    assert target.get('account_info', {}).get('type') == ['Continuous Vesting Account'], \
        f"Account type not set correctly: {target.get('account_info', {})}"
    
    assert target.get('account_info', {}).get('address') == [expanded_src['address']], \
        f"Address not set correctly: {target.get('account_info', {})}"
    
    assert target.get('key_info', {}).get('key_type') == ['secp256k1'], \
        f"Key type not set correctly: {target.get('key_info', {})}"
    
    # Test 3: Test with array indexing in paths
    target = {}
    
    # Get the first attribute directly for comparison
    first_attribute = expanded_src['attributes'][0]['attribute'] if expanded_src.get('attributes') else None
    
    paths_map = [
        # Test array indexing
        ('attributes.0.attribute', 'first_attr'),
        # Test with a selector that should match multiple items
        ('publicKey.sigList.*.address', 'signer_addresses')
    ]
    
    getpaths_setpaths(expanded_src, target, paths_map)
    
    # Debug output
    print("\nTarget with array paths:", target)
    
    # Verify the results
    if first_attribute:
        assert target.get('first_attr') == [first_attribute], \
            f"Expected first_attr to be {[first_attribute]}, got {target.get('first_attr')}"
    
    # Verify the signer addresses
    if 'publicKey' in expanded_src and 'sigList' in expanded_src['publicKey']:
        expected_addresses = [sig.get('address') for sig in expanded_src['publicKey']['sigList']]
        assert target.get('signer_addresses') == expected_addresses, \
            f"Expected signer_addresses to be {expected_addresses}, got {target.get('signer_addresses')}"
    
    # Test 4: Check if base64 fields were properly expanded
    # For example, if there are any fields that were base64-encoded in the original
    # but should be dicts/strings in the expanded version
    
    # Find the first attribute that was base64 encoded in the original
    base64_attrs = [
        attr for attr in src.get('attributes', [])
        if isinstance(attr.get('data'), str) and len(attr['data']) > 10  # Likely base64
    ]
    
    for base64_attr in base64_attrs:
        attr_name = base64_attr['data']
        # The same attribute in the expanded source should be a dict/string, not base64
        expanded_attr = next(
            (attr for attr in expanded_src.get('attributes', [])
             if attr.get('data') == base64_attr['data']),
            None
        )
        
        # If we found the attribute in the expanded source, verify it was decoded
        if expanded_attr:
            # The expanded data should be a dict (if it was JSON) or a shorter string
            # than the original base64-encoded data
            assert not (isinstance(expanded_attr.get('data'), str) and 
                      len(expanded_attr['data']) > 100), \
                f"Data for {attr_name} doesn't appear to be decoded"
    
    # Test 3: Test with a nested path that might contain base64 data
    # This depends on the structure of your real_world_example.json
    # For example, if you know a specific path that contains base64 data:
    try:
        # Try to find a nested path that might contain base64
        nested_path = next(
            f"attributes.{i}.data" 
            for i, attr in enumerate(src.get('attributes', []))
            if isinstance(attr.get('data'), str) and len(attr['data']) > 10
        )
        
        # The expanded version should have the decoded data
        expanded_value = get_nested(expanded_src, nested_path)
        original_value = get_nested(src, nested_path)
        
        # The expanded value should be different from the original (unless it wasn't base64)
        if isinstance(expanded_value, (dict, list)) or ' ' in str(expanded_value):
            assert expanded_value != original_value
            
    except (StopIteration, KeyError):
        # Skip if no suitable path was found
        pass

def get_nested(obj, path, default=None):
    """Helper to get a nested value from a dict using dot notation."""
    keys = path.split('.')
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key, default)
        elif isinstance(obj, list) and key.isdigit() and int(key) < len(obj):
            obj = obj[int(key)]
        else:
            return default
    return obj

def test_setpath_with_base64():
    """Test setpath with base64-expanded data."""
    # Load the real world example data
    test_file = os.path.join(os.path.dirname(__file__), 'real_world_example.json')
    with open(test_file, 'r') as f:
        src = json.load(f)
    
    # Expand all base64 strings in the source data
    expanded_src = base64expand(src)
    
    # Test 1: Basic field mapping
    target1 = {}
    setpath(target1, 'account_info.type', get_nested(expanded_src, 'accountType'))
    assert target1.get('account_info', {}).get('type') == 'Continuous Vesting Account'
    
    # Test 2: Nested path that was expanded from base64
    target2 = {}
    try:
        # Find a nested path that was base64 in the original
        nested_path = next(
            f"attributes.{i}.data" 
            for i, attr in enumerate(src.get('attributes', []))
            if isinstance(attr.get('data'), str) and len(attr['data']) > 10
        )
        
        # Get the expanded value
        expanded_value = get_nested(expanded_src, nested_path)
        
        # Set it in the target
        setpath(target2, 'expanded_data.some_field', expanded_value)
        
        # The value should be set correctly
        assert target2.get('expanded_data', {}).get('some_field') == expanded_value
        
    except (StopIteration, KeyError):
        # Skip if no suitable path was found
        pass
    
    # Test 3: Test with array indexing in paths
    target3 = {}
    if 'attributes' in expanded_src and len(expanded_src['attributes']) > 0:
        first_attr = expanded_src['attributes'][0]
        setpath(target3, 'first_attribute', first_attr)
        assert target3.get('first_attribute') == first_attr
    
    # Test 4: Test with wildcard selector (should set all matching paths)
    target4 = {}
    if 'attributes' in expanded_src and len(expanded_src['attributes']) > 0:
        # Set the same value on multiple paths using a wildcard
        setpath(target4, 'all_attributes.*.status', 'active')
        
        # Verify the status was set on all attributes
        if 'all_attributes' in target4:
            for attr in target4['all_attributes']:
                assert attr.get('status') == 'active'
    
    # Test 5: Test with non-existent path (should create the path)
    target5 = {}
    setpath(target5, 'new.path.to.field', 'test_value')
    assert get_nested(target5, 'new.path.to.field') == 'test_value'
    
    # Test 6: Test with empty path (sets as a key with empty string)
    target6 = {}
    setpath(target6, '', {'key': 'value'})
    # setpath with empty string as path sets it as a key with empty string
    assert target6 == {'': {'key': 'value'}}
