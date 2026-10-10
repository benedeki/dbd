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

import json

import pytest

from dbd.core.expandable_config import ExpandableConfig


class StubSecretReader:
    def __init__(self, secrets: dict[str, str]):
        self.secrets = secrets

    def get_secret(self, name: str) -> str | None:
        return self.secrets.get(name)


def create_config(tmp_path, data: dict, cli_parameters: dict[str, str] | None = None) -> ExpandableConfig:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(data), encoding="utf-8")
    return ExpandableConfig(str(config_path), cli_parameters or {})


def test_loads_json_object(tmp_path):
    config = create_config(tmp_path, {"name": "example", "enabled": True})

    assert config._data == {"name": "example", "enabled": True}


def test_rejects_non_object_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('["not", "an", "object"]', encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a JSON object"):
        ExpandableConfig(str(config_path), {})


def test_expand_resolves_file_references_relative_to_config(tmp_path):
    included_path = tmp_path / "included.json"
    included_path.write_text('{"value": "from included file"}', encoding="utf-8")
    config = create_config(tmp_path, {"included": "__FILE(included.json)"})

    config.expand()

    assert config._data == {"included": {"value": "from included file"}}


def test_expand_resolves_nested_file_references(tmp_path):
    included_path = tmp_path / "included.json"
    included_path.write_text('{"value": "included value"}', encoding="utf-8")
    config = create_config(
        tmp_path,
        {"items": ["__FILE(included.json)", {"value": "__FILE(included.json)"}]},
    )

    config.expand()

    assert config._data == {
        "items": [
            {"value": "included value"},
            {"value": {"value": "included value"}},
        ]
    }


def test_expand_resolves_references_in_nested_dictionaries(tmp_path):
    config = create_config(
        tmp_path,
        {"database": {"password": "__SECRET(database-password)", "name": "__CLI(name)"}},
        {"name": "example"},
    )

    config.expand(StubSecretReader({"database-password": "secret-value"}))

    assert config._data == {
        "database": {"password": "secret-value", "name": "example"},
    }


def test_expand_preserves_non_reference_values(tmp_path):
    config = create_config(
        tmp_path,
        {
            "text": "ordinary text",
            "partial": "prefix __CLI(name)",
            "number": 42,
            "items": [True, None, "ordinary item"],
        },
    )

    config.expand()

    assert config._data == {
        "text": "ordinary text",
        "partial": "prefix __CLI(name)",
        "number": 42,
        "items": [True, None, "ordinary item"],
    }


def test_expand_resolves_file_reference_to_scalar(tmp_path):
    included_path = tmp_path / "included.json"
    included_path.write_text('"included value"', encoding="utf-8")
    config = create_config(tmp_path, {"included": "__FILE(included.json)"})

    config.expand()

    assert config._data == {"included": "included value"}


def test_expand_resolves_secret_references(tmp_path):
    config = create_config(
        tmp_path,
        {"password": "__SECRET(database-password)", "items": ["__SECRET(database-password)"]},
    )

    config.expand(StubSecretReader({"database-password": "secret-value"}))

    assert config._data == {"password": "secret-value", "items": ["secret-value"]}


def test_expand_resolves_cli_references(tmp_path):
    config = create_config(tmp_path, {"name": "__CLI(name)"}, {"name": "example"})

    config.expand()

    assert config._data == {"name": "example"}


def test_expand_resolves_environment_references(tmp_path, monkeypatch):
    monkeypatch.setenv("DBD_NAME", "example")
    config = create_config(tmp_path, {"name": "__ENV(DBD_NAME)"})

    config.expand()

    assert config._data == {"name": "example"}


def test_expand_resolves_config_references(tmp_path):
    config = create_config(tmp_path, {"source": "example", "copy": "__CFG(source)"})

    config.expand()

    assert config._data == {"source": "example", "copy": "example"}


def test_expand_supports_expanding_a_branch(tmp_path):
    config = create_config(tmp_path, {"nested": {"name": "__CLI(name)"}}, {"name": "example"})

    config.expand(branch="nested")

    assert config._data == {"nested": {"name": "example"}}


def test_expand_rejects_missing_branch(tmp_path):
    config = create_config(tmp_path, {"nested": {"name": "example"}})

    with pytest.raises(KeyError):
        config.expand(branch="missing")


def test_expand_rejects_missing_secret_reader(tmp_path):
    config = create_config(tmp_path, {"password": "__SECRET(database-password)"})

    with pytest.raises(ValueError, match="Secret reader is not provided"):
        config.expand()


def test_expand_rejects_missing_cli_parameter(tmp_path):
    config = create_config(tmp_path, {"name": "__CLI(name)"})

    with pytest.raises(ValueError, match="CLI parameter 'name' has not been provided"):
        config.expand()


def test_expand_rejects_missing_environment_variable(tmp_path, monkeypatch):
    monkeypatch.delenv("DBD_NAME", raising=False)
    config = create_config(tmp_path, {"name": "__ENV(DBD_NAME)"})

    with pytest.raises(ValueError, match="Environment variable 'DBD_NAME' is not set"):
        config.expand()


def test_expand_rejects_unknown_reference_type(tmp_path):
    config = create_config(tmp_path, {"value": "__UNKNOWN(value)"})

    with pytest.raises(ValueError, match="Unknown reference type 'UNKNOWN'"):
        config.expand()
