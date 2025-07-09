import pytest
import json
from base64expand import base64expand


def test_base64expand_simple_string():
    # base64 for 'hello world' is 'aGVsbG8gd29ybGQ='
    assert base64expand('aGVsbG8gd29ybGQ=') == 'hello world'


def test_base64expand_json():
    # base64 for '{"foo": "bar"}' is 'eyJmb28iOiAiYmFyIn0='
    assert base64expand('eyJmb28iOiAiYmFyIn0=') == {'foo': 'bar'}


def test_base64expand_nested():
    # base64 for base64 for 'hello' is 'aGVsbG8=' -> 'YUdWc2JHOD0='
    assert base64expand('YUdWc2JHOD0=') == 'hello'


def test_base64expand_list():
    # List with base64 and plain
    data = ['aGVsbG8=', 'world']
    assert base64expand(data) == ['hello', 'world']


def test_base64expand_dict():
    # Dict with base64 value
    data = {'msg': 'aGVsbG8='}
    assert base64expand(data) == {'msg': 'hello'}


def test_base64expand_non_utf8():
    # base64 for bytes that are not valid utf-8
    # e.g. 0xff 0xfe 0xfd -> '//79'
    assert base64expand('//79') == '//79'


def test_base64expand_json_with_base64_value():
    # JSON with a base64 value inside
    # {"data": "aGVsbG8="} -> eyJkYXRhIjogImhlbGxvIn0=
    assert base64expand('eyJkYXRhIjogImhlbGxvIn0=') == {'data': 'hello'}


def test_base64expand_deeply_nested():
    import base64
    # Build the nested structure programmatically to ensure correctness
    msg = 'hello'
    msg_b64 = base64.b64encode(msg.encode('utf-8')).decode('ascii')  # 'aGVsbG8='
    inner = {'msg': msg_b64}
    inner_json = json.dumps(inner)
    inner_b64 = base64.b64encode(inner_json.encode('utf-8')).decode('ascii')
    outer = {'inner': inner_b64}
    outer_json = json.dumps(outer)
    outer_b64 = base64.b64encode(outer_json.encode('utf-8')).decode('ascii')
    deeply_nested = {'outer': outer_b64}
    assert base64expand(deeply_nested) == {'outer': {'inner': {'msg': 'hello'}}}


def test_base64expand_double_base64():
    import base64
    # Start with a JSON object
    obj = {'foo': 'bar'}
    # Encode as JSON, then base64
    json1 = json.dumps(obj)
    b64_1 = base64.b64encode(json1.encode('utf-8')).decode('ascii')
    # Encode the base64 string again as base64
    b64_2 = base64.b64encode(b64_1.encode('utf-8')).decode('ascii')
    # The function should fully expand to the original object
    assert base64expand(b64_2) == obj
