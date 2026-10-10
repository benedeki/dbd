# Copyright 2026 David Benedeki, All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import pytest

from dbd.core.simple_config import SimpleConfig


def test_has_key_reports_whether_key_exists():
    config = SimpleConfig({"name": "example"})

    assert "name" in config
    assert "missing" not in config


def test_get_returns_configured_value():
    value = {"nested": ["value"]}
    config = SimpleConfig({"value": value})

    assert config.get("value") is value


def test_get_raises_for_missing_key():
    with pytest.raises(KeyError):
        SimpleConfig({}).get("missing")


def test_get_as_str_returns_value_and_joins_lists():
    config = SimpleConfig({"name": "example", "items": ["one", 2, True]})

    assert config.get_as_str("name") == "example"
    assert config.get_as_str("items") == "one\n2\nTrue"
    assert SimpleConfig({"value": 42}).get_as_str("value") == "42"


def test_get_as_str_uses_default():
    assert SimpleConfig({}).get_as_str("name", "default") == "default"


@pytest.mark.parametrize(
    ("getter", "value", "expected"),
    [
        ("get_as_int", "42", 42),
        ("get_as_bool", 1, True),
        ("get_as_float", "3.14", 3.14),
    ],
)
def test_scalar_getters_convert_values(getter, value, expected):
    config = SimpleConfig({"value": value})

    assert getattr(config, getter)("value") == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        ("true", True),
        (" YES ", True),
        ("1", True),
        ("false", False),
        ("no", False),
        ("0", False),
    ],
)
def test_get_as_bool_converts_supported_values(value, expected):
    assert SimpleConfig({"value": value}).get_as_bool("value") is expected


def test_get_as_bool_rejects_invalid_value():
    with pytest.raises(ValueError, match="Cannot interpret 'maybe' as boolean"):
        SimpleConfig({"value": "maybe"}).get_as_bool("value")


def test_scalar_getters_use_defaults():
    config = SimpleConfig({})

    assert config.get_as_int("value", 42) == 42
    assert config.get_as_bool("value", True) is True
    assert config.get_as_float("value", 3.14) == 3.14


def test_get_as_list_returns_list_or_wraps_scalar():
    config = SimpleConfig({"items": ["one", "two"], "item": "one"})

    assert config.get_as_list("items") == ["one", "two"]
    assert config.get_as_list("item") == ["one"]
    assert config.get_as_list("missing", ["default"]) == ["default"]


def test_get_as_list_returns_configured_list_reference():
    value = ["one"]
    config = SimpleConfig({"items": value})

    assert config.get_as_list("items") is value


def test_get_as_config_returns_config_for_mapping():
    config = SimpleConfig({"nested": {"name": "example"}})

    nested = config.get_as_config("nested")

    assert isinstance(nested, SimpleConfig)
    assert nested._data == {"name": "example"}


def test_get_as_dict_returns_mapping_reference():
    value = {"nested": ["value"]}

    assert SimpleConfig({"value": value}).get_as_dict("value") is value


@pytest.mark.parametrize("value", ["example", 42, True, 3.14])
def test_get_as_dict_rejects_scalar_value(value):
    with pytest.raises(ValueError, match="is not a dictionary"):
        SimpleConfig({"value": value}).get_as_dict("value")


@pytest.mark.parametrize("value", ["example", 42, True, 3.14])
def test_get_as_config_rejects_scalar_value(value):
    with pytest.raises(ValueError, match="is not a dictionary"):
        SimpleConfig({"value": value}).get_as_config("value")


@pytest.mark.parametrize(
    "getter",
    [
        "get_as_str",
        "get_as_int",
        "get_as_bool",
        "get_as_float",
        "get_as_list",
        "get_as_dict",
        "get_as_config",
    ],
)
def test_getters_raise_for_missing_values(getter):
    with pytest.raises(KeyError, match="Configuration key 'missing' not found"):
        getattr(SimpleConfig({}), getter)("missing")
