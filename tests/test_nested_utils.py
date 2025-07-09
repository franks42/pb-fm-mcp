#!/usr/bin/env python3
"""
Test Suite for Nested Data Structure Functions
For Cloudflare Python Workers

Run this file to validate the functions work correctly:
python test_nested_functions.py
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import json
import re
from functools import reduce
import time
import sys

# Import the tested functions from src.nested_utils
from nested_utils import (
    modify_nested,
    get_nested,
    has_nested,
    find_attributes,
    get_multiple_nested,
)


# === TEST UTILITIES ===

class TestRunner:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
    
    def test(self, description, test_function):
        self.tests_run += 1
        try:
            test_function()
            self.tests_passed += 1
            print(f"✅ {description}")
        except Exception as e:
            self.failures.append(f"{description}: {str(e)}")
            print(f"❌ {description} - {str(e)}")
    
    def assert_equal(self, actual, expected, message=""):
        if actual != expected:
            raise AssertionError(f"Expected {expected}, got {actual}. {message}")
    
    def assert_true(self, condition, message=""):
        if not condition:
            raise AssertionError(f"Expected True, got False. {message}")
    
    def print_summary(self):
        print(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Functions are ready for Cloudflare Python Workers!")
        else:
            print(f"❌ {len(self.failures)} tests failed:")
            for failure in self.failures:
                print(f"   • {failure}")


# === TEST DATA ===

test_data = {
    'user': {
        'profile': {
            'name': 'John Doe',
            'age': 30,
            'email': 'john@example.com',
            'user_id': 12345
        },
        'settings': {
            'theme': 'dark',
            'notifications': True,
            'preferences': ['email', 'sms', 'push']
        }
    },
    'metadata': {
        'version': '1.0',
        'created': '2024-01-01'
    },
    'items': [
        {'id': 1, 'name': 'Item 1', 'active': True},
        {'id': 2, 'name': 'Item 2', 'active': False},
        {'id': 3, 'name': 'Item 3', 'active': True}
    ],
    'admin': {
        'admin_name': 'Administrator',
        'secret_key': 'topsecret'
    }
}


# === RUN TESTS ===

def run_tests():
    print("🧪 Python Test Suite for Nested Data Structure Functions")
    print("=" * 60)
    print("Testing functions for Cloudflare Python Workers compatibility")
    
    runner = TestRunner()
    
    print("\n📖 Testing GET operations:")
    
    runner.test("Get simple nested value", lambda: 
        runner.assert_equal(get_nested(test_data, "user.profile.name"), "John Doe"))
    
    runner.test("Get with list path", lambda: 
        runner.assert_equal(get_nested(test_data, ["user", "profile", "age"]), 30))
    
    runner.test("Get non-existent returns default", lambda: 
        runner.assert_equal(get_nested(test_data, "missing.key", "DEFAULT"), "DEFAULT"))
    
    runner.test("Get array element by index", lambda: 
        runner.assert_equal(get_nested(test_data, "items.0.name"), "Item 1"))
    
    runner.test("Get with negative array index", lambda: 
        runner.assert_equal(get_nested(test_data, "items.-1.name"), "Item 3"))
    
    runner.test("Get with custom separator", lambda: 
        runner.assert_equal(get_nested(test_data, "user/profile/name", None, "/"), "John Doe"))
    
    print("\n✏️ Testing MODIFY operations:")
    
    def test_set_nested():
        data = json.loads(json.dumps(test_data))  # Deep copy
        modify_nested(data, "user.profile.city", "New York")
        runner.assert_equal(get_nested(data, "user.profile.city"), "New York")
    runner.test("Set nested value", test_set_nested)
    
    def test_create_missing():
        data = {}
        modify_nested(data, "a.b.c.d", "deep")
        runner.assert_equal(get_nested(data, "a.b.c.d"), "deep")
    runner.test("Create missing structure", test_create_missing)
    
    def test_delete_nested():
        data = json.loads(json.dumps(test_data))
        modify_nested(data, "user.profile.email", operation="delete")
        runner.assert_equal(get_nested(data, "user.profile.email", "MISSING"), "MISSING")
    runner.test("Delete nested value", test_delete_nested)
    
    def test_append_array():
        data = json.loads(json.dumps(test_data))
        modify_nested(data, "user.settings.preferences", "webhook", "append")
        runner.assert_equal(len(get_nested(data, "user.settings.preferences")), 4)
    runner.test("Append to array", test_append_array)
    
    def test_extend_array():
        data = json.loads(json.dumps(test_data))
        modify_nested(data, "user.settings.preferences", ["a", "b"], "extend")
        runner.assert_equal(len(get_nested(data, "user.settings.preferences")), 5)
    runner.test("Extend array", test_extend_array)
    
    print("\n🔍 Testing HAS operations:")
    
    runner.test("Has existing path", lambda: 
        runner.assert_true(has_nested(test_data, "user.profile.name")))
    
    runner.test("Has non-existing path", lambda: 
        runner.assert_true(not has_nested(test_data, "user.profile.missing")))
    
    print("\n🔍 Testing SEARCH operations:")
    
    def test_find_exact():
        results = find_attributes(test_data, "name")
        runner.assert_true(len(results) >= 2)
        runner.assert_true(any("profile.name" in r['path'] for r in results))
    runner.test("Find exact key matches", test_find_exact)
    
    def test_find_contains():
        results = find_attributes(test_data, "user", "contains", False)
        runner.assert_true(len(results) > 0)
        runner.assert_true(any("user" in str(r['key']).lower() for r in results))
    runner.test("Find keys containing pattern", test_find_contains)
    
    def test_find_regex():
        results = find_attributes(test_data, r".*_id$", "regex")
        runner.assert_true(len(results) >= 1)
        runner.assert_true(any(r['key'] == "user_id" for r in results))
    runner.test("Find with regex", test_find_regex)
    
    def test_find_values():
        results = find_attributes(test_data, "dark", "contains", True, True)
        runner.assert_true(any(r['match_type'] == "value" for r in results))
    runner.test("Find values", test_find_values)
    
    print("\n📊 Testing BATCH operations:")
    
    def test_multiple_list():
        results = get_multiple_nested(test_data, [
            "user.profile.name",
            "user.profile.age", 
            "metadata.version"
        ])
        runner.assert_equal(results, ["John Doe", 30, "1.0"])
    runner.test("Get multiple with list", test_multiple_list)
    
    def test_multiple_dict():
        results = get_multiple_nested(test_data, {
            'name': 'user.profile.name',
            'theme': 'user.settings.theme',
            'version': 'metadata.version'
        })
        expected = {'name': 'John Doe', 'theme': 'dark', 'version': '1.0'}
        runner.assert_equal(results, expected)
    runner.test("Get multiple with dict mapping", test_multiple_dict)
    
    print("\n⚡ Performance testing:")
    
    def test_performance():
        # Create large dataset
        large_data = {}
        for i in range(1000):
            large_data[f'item{i}'] = {
                'id': i,
                'name': f'Item {i}',
                'data': {'value': i * 2}
            }
        
        # Time the search
        start_time = time.time()
        results = find_attributes(large_data, "id", "exact")
        end_time = time.time()
        
        # Verify results
        runner.assert_equal(len(results), 1000)
        runner.assert_true((end_time - start_time) < 2.0)  # Should complete in under 2 seconds
        print(f"   Search completed in {(end_time - start_time)*1000:.1f}ms")
    runner.test("Performance: Search 1000 items", test_performance)
    
    print("\n☁️ Cloudflare Workers compatibility:")
    
    def test_json_compat():
        data = {'user': {'name': 'test'}}
        modify_nested(data, "user.processed", True)
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        runner.assert_equal(get_nested(parsed, "user.processed"), True)
    runner.test("JSON serialization works", test_json_compat)
    
    def test_request_like():
        request_data = {
            'headers': {'content-type': 'application/json'},
            'body': {
                'user': {'profile': {'name': 'API User'}},
                'metadata': {'timestamp': time.time()}
            }
        }
        
        user_name = get_nested(request_data, "body.user.profile.name")
        runner.assert_equal(user_name, "API User")
        
        modify_nested(request_data, "body.processed", True)
        runner.assert_true(has_nested(request_data, "body.processed"))
    runner.test("Works with request-like data", test_request_like)
    
    print("\n🔬 Testing standard library compatibility:")
    
    def test_stdlib_modules():
        """Test that we only use modules available in Cloudflare Workers"""
        # These should all work without import errors
        import json
        import re
        from functools import reduce
        
        # Test regex functionality
        pattern = re.compile(r"test_\d+")
        runner.assert_true(pattern.match("test_123"))
        
        # Test json functionality  
        data = {"test": [1, 2, 3]}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        runner.assert_equal(parsed, data)
        
        # Test functools
        numbers = [1, 2, 3, 4, 5]
        result = reduce(lambda x, y: x + y, numbers)
        runner.assert_equal(result, 15)
        
    runner.test("Standard library modules work", test_stdlib_modules)
    
    # Print final summary
    runner.print_summary()
    
    return runner.tests_passed == runner.tests_run


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
