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
from dbd.implementations.file.secret_reader import SecretReader


def test_reads_secrets_from_json_file(tmp_path):
    secrets_path = tmp_path / "secrets.json"
    secrets_path.write_text(
        json.dumps({"password": "secret-value", "port": 5432, "enabled": True}),
        encoding="utf-8",
    )

    reader = SecretReader(Config({"file_name": str(secrets_path)}))

    assert reader.get_secret("password") == "secret-value"
    assert reader.get_secret("port") == "5432"
    assert reader.get_secret("enabled") == "True"


def test_returns_dictionary_secrets_without_string_conversion(tmp_path):
    secrets_path = tmp_path / "secrets.json"
    nested_secret = {"username": "db-user", "password": "secret-value"}
    secrets_path.write_text(json.dumps({"database": nested_secret}), encoding="utf-8")

    reader = SecretReader(Config({"file_name": str(secrets_path), "type": "json"}))

    assert reader.get_secret("database") == nested_secret


def test_returns_none_for_missing_secret(tmp_path):
    secrets_path = tmp_path / "secrets.json"
    secrets_path.write_text("{}", encoding="utf-8")
    reader = SecretReader(Config({"file_name": str(secrets_path)}))

    assert reader.get_secret("missing") is None


def test_rejects_unsupported_file_type(tmp_path):
    secrets_path = tmp_path / "secrets.yaml"
    secrets_path.write_text("password: secret-value", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file type: yaml"):
        SecretReader(Config({"file_name": str(secrets_path), "type": "yaml"}))


def test_rejects_non_object_json(tmp_path):
    secrets_path = tmp_path / "secrets.json"
    secrets_path.write_text('["not", "an", "object"]', encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a JSON object"):
        SecretReader(Config({"file_name": str(secrets_path)}))
