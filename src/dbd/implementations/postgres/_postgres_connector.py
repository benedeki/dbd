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

from typing import Any

import psycopg

from dbd.core.simple_config import SimpleConfig


class _PostgresConnector:
    @property
    def one_transaction(self) -> bool:
        return self._one_transaction

    def __init__(self, config: SimpleConfig, one_transaction: bool):
        self._one_transaction = one_transaction
        self._host = config.get_as_str("host")
        self._port = config.get_as_int("port", 5432)
        self._dbname = config.get_as_str("dbname")
        self._user = config.get_as_str("user")
        self._password = config.get_as_str("password")
        self._sslmode = config.get_as_str("sslmode", "prefer")
        self._sslcert = config.get_as_str("sslcert", "")
        self._connect_timeout = config.get_as_int("connect_timeout", 10)
        self._connection: psycopg.Connection | None = None
        self._transaction_failed = False

    def _connect(self) -> psycopg.Connection:
        connection_parameters: dict[str, Any] = {
            "host": self._host,
            "port": self._port,
            "dbname": self._dbname,
            "user": self._user,
            "password": self._password,
            "sslmode": self._sslmode,
        }
        if self._sslcert:
            connection_parameters["sslcert"] = self._sslcert
        if self._connect_timeout > 0:
            connection_parameters["connect_timeout"] = self._connect_timeout
        return psycopg.connect(**connection_parameters)
