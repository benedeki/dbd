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

from unittest.mock import MagicMock, patch

import pytest

from dbd.core.config import Config
from dbd.core.operation_status import OpFailure, OpSuccess
from dbd.implementations.postgres.destination_system import DestinationSystem


@pytest.fixture
def config() -> Config:
    return Config(
        {
            "connection": {
                "host": "localhost",
                "port": 5432,
                "dbname": "dbd",
                "user": "dbd-user",
                "password": "secret",
            },
        }
    )


def test_executes_source_using_configured_connection(config: Config):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value

    with patch("psycopg.connect", return_value=connection) as connect:
        destination = DestinationSystem(config)
        destination.init()
        result = destination.deploy("CREATE TABLE example (id integer);")
        destination.close()

    connect.assert_called_once_with(
        host="localhost",
        port=5432,
        dbname="dbd",
        user="dbd-user",
        password="secret",
    )
    cursor.execute.assert_called_once_with("CREATE TABLE example (id integer);")
    assert result == OpSuccess()


def test_returns_failure_when_postgres_rejects_source(config: Config):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value

    with patch("psycopg.connect", return_value=connection), patch(
        "psycopg.Error", DatabaseError
    ):
        cursor.execute.side_effect = DatabaseError("syntax error")
        destination = DestinationSystem(config)
        destination.init()
        result = destination.deploy("INVALID SQL")
        destination.close()

    assert result == OpFailure("syntax error")
    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
    connection.close.assert_called_once_with()


def test_rejects_deploy_before_initializing_one_transaction(config: Config):
    destination = DestinationSystem(config)

    result = destination.deploy("CREATE TABLE example (id integer);")

    assert result == OpFailure("No active connection for one_transaction mode.")
    destination.close()


def test_returns_failure_for_individual_transaction_error():
    config = Config(
        {
            "connection": {
                "host": "localhost",
                "dbname": "dbd",
                "user": "dbd-user",
                "password": "secret",
            },
            "one_transaction": False,
        }
    )
    connection = MagicMock()
    connection.__enter__.return_value = connection
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = DatabaseError("syntax error")

    with patch("psycopg.connect", return_value=connection), patch(
        "psycopg.Error", DatabaseError
    ):
        result = DestinationSystem(config).deploy("INVALID SQL")

    assert result == OpFailure("syntax error")


def test_executes_repeated_deploys_in_one_transaction(config: Config):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value

    with patch("psycopg.connect", return_value=connection) as connect:
        destination = DestinationSystem(config)
        destination.init()
        first_result = destination.deploy("CREATE TABLE example (id integer);")
        second_result = destination.deploy("INSERT INTO example VALUES (1);")
        destination.close()

    connect.assert_called_once()
    assert cursor.execute.call_count == 2
    connection.commit.assert_called_once_with()
    connection.close.assert_called_once_with()
    assert first_result == OpSuccess()
    assert second_result == OpSuccess()


def test_executes_each_deploy_in_its_own_transaction():
    config = Config(
        {
            "connection": {
                "host": "localhost",
                "dbname": "dbd",
                "user": "dbd-user",
                "password": "secret",
            },
            "one_transaction": False,
        }
    )
    connections = [MagicMock(), MagicMock()]
    with patch("psycopg.connect", side_effect=connections) as connect:
        destination = DestinationSystem(config)
        first_result = destination.deploy("CREATE TABLE example (id integer);")
        second_result = destination.deploy("INSERT INTO example VALUES (1);")

    assert connect.call_count == 2
    assert connections[0].__exit__.call_count == 1
    assert connections[1].__exit__.call_count == 1
    assert first_result == OpSuccess()
    assert second_result == OpSuccess()


class DatabaseError(Exception):
    pass
