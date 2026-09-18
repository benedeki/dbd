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

import json

import pytest

from dbd.core.config import Config


class StubSecretReader:
    def __init__(self, secrets: dict[str, str]):
        self.secrets = secrets

    def get_secret(self, name: str) -> str | None:
        return self.secrets.get(name)


def test_from_file_loads_json_object(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"name": "example", "enabled": true}', encoding="utf-8")

    config = Config.from_file(str(config_path))

    assert config._data == {"name": "example", "enabled": True}


def test_from_file_expands_nested_file_references_relative_to_config(tmp_path):
    included_path = tmp_path / "included.json"
    included_path.write_text('{"value": "from included file"}', encoding="utf-8")
    config_path = tmp_path / "config.json"
    config_path.write_text('{"included": "__FILE(included.json)"}', encoding="utf-8")

    config = Config.from_file(str(config_path))

    assert config._data == {"included": {"value": "from included file"}}


def test_from_file_expands_file_references_in_nested_values(tmp_path):
    included_path = tmp_path / "included.json"
    included_path.write_text('{"value": "included value"}', encoding="utf-8")
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"items": ["__FILE(included.json)", {"value": "__FILE(included.json)"}]}),
        encoding="utf-8",
    )

    config = Config.from_file(str(config_path))

    assert config._data == {
        "items": [
            {"value": "included value"},
            {"value": {"value": "included value"}},
        ]
    }


def test_from_file_expands_secret_references(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"password": "__SECRET(database-password)"}', encoding="utf-8")
    secret_reader = StubSecretReader({"database-password": "secret-value"})

    config = Config.from_file(str(config_path), secret_reader=secret_reader)

    assert config._data == {"password": "secret-value"}


def test_from_file_preserves_unresolved_references(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        '{"missing_secret": "__SECRET(missing)", "unknown": "__ENVIRONMENT(value)"}',
        encoding="utf-8",
    )
    secret_reader = StubSecretReader({})

    config = Config.from_file(str(config_path), secret_reader=secret_reader)

    assert config._data == {
        "missing_secret": "__SECRET(missing)",
        "unknown": "__ENVIRONMENT(value)",
    }


def test_from_file_rejects_non_object_json(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('["not", "an", "object"]', encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a JSON object"):
        Config.from_file(str(config_path))


def test_expand_expands_file_and_secret_references_from_current_directory(tmp_path, monkeypatch):
    included_path = tmp_path / "included.json"
    included_path.write_text('{"value": "from included file"}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    config = Config(
        {
            "included": "__FILE(included.json)",
            "password": "__SECRET(database-password)",
            "items": ["__SECRET(database-password)"],
        }
    )

    config.expand(StubSecretReader({"database-password": "secret-value"}))

    assert config._data == {
        "included": {"value": "from included file"},
        "password": "secret-value",
        "items": ["secret-value"],
    }


def test_expand_preserves_unresolved_references():
    config = Config(
        {
            "missing_secret": "__SECRET(missing)",
            "unknown": "__ENVIRONMENT(value)",
            "partial": "prefix __SECRET(value)",
        }
    )

    config.expand(StubSecretReader({}))

    assert config._data == {
        "missing_secret": "__SECRET(missing)",
        "unknown": "__ENVIRONMENT(value)",
        "partial": "prefix __SECRET(value)",
    }
