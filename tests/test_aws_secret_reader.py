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

from unittest.mock import Mock, patch

import pytest

from dbd.core.config import Config
from dbd.implementations.aws.secret_reader import SecretReader


def test_creates_secrets_manager_client_with_configured_region():
    client = Mock()

    with patch("dbd.implementations.aws.secret_reader.boto3.client", return_value=client) as client_factory:
        reader = SecretReader(Config({"region_name": "eu-west-1"}))

    client_factory.assert_called_once_with("secretsmanager", region_name="eu-west-1")
    assert reader.region_name == "eu-west-1"
    assert reader.client is client


def test_returns_dictionary_from_secret_string():
    client = Mock()
    client.get_secret_value.return_value = {"SecretString": '{"username": "db-user"}'}
    reader = _create_reader(client)

    assert reader.get_secret("database") == {"username": "db-user"}
    client.get_secret_value.assert_called_once_with(SecretId="database")


def test_returns_decoded_scalar_secret_string():
    client = Mock()
    client.get_secret_value.return_value = {"SecretString": '"secret-value"'}
    reader = _create_reader(client)

    assert reader.get_secret("password") == "secret-value"


def test_returns_list_from_secret_string():
    client = Mock()
    client.get_secret_value.return_value = {"SecretString": '["secret-value", 42]'}
    reader = _create_reader(client)

    assert reader.get_secret("passwords") == ["secret-value", 42]


def test_returns_undecodable_secret_string_as_is():
    client = Mock()
    client.get_secret_value.return_value = {"SecretString": "secret-value"}
    reader = _create_reader(client)

    assert reader.get_secret("password") == "secret-value"


def test_returns_none_when_secret_string_is_missing():
    client = Mock()
    client.get_secret_value.return_value = {}
    reader = _create_reader(client)

    assert reader.get_secret("missing") is None


def test_returns_none_when_secret_is_binary():
    client = Mock()
    client.get_secret_value.return_value = {"SecretBinary": b"secret-value"}
    reader = _create_reader(client)

    with pytest.raises(ValueError, match="Secret 'binary-secret' is binary, which is not supported."):
        reader.get_secret("binary-secret")

def test_returns_none_when_secret_is_not_found():
    class ResourceNotFoundError(Exception):
        pass

    client = Mock()
    client.exceptions.ResourceNotFoundException = ResourceNotFoundError
    client.get_secret_value.side_effect = ResourceNotFoundError
    reader = _create_reader(client)

    assert reader.get_secret("missing") is None


def _create_reader(client: Mock) -> SecretReader:
    with patch("dbd.implementations.aws.secret_reader.boto3.client", return_value=client):
        return SecretReader(Config({"region_name": "eu-west-1"}))
