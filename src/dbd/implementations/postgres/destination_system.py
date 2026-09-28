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

from dbd.abstract.abstract_destination_system import AbstractDestinationSystem
from dbd.core.config import Config
from dbd.core.operation_status import OperationStatus, OpFailure, OpSuccess


class DestinationSystem(AbstractDestinationSystem):
    @property
    def one_transaction(self) -> bool:
        return self._one_transaction

    def __init__(self, config: Config):
        super().__init__(config)
        self._one_transaction = config.get_as_bool("one_transaction", True)
        connection_config = config.get_as_config("connection")
        self._host = connection_config.get_as_str("host")
        self._port = connection_config.get_as_int("port", 5432)
        self._dbname = connection_config.get_as_str("dbname")
        self._user = connection_config.get_as_str("user")
        self._password = connection_config.get_as_str("password")
        self._sslmode = connection_config.get_as_str("sslmode", "prefer")
        self._sslcert = connection_config.get_as_str("sslcert", "")
        self._connection: psycopg.Connection | None = None
        self._transaction_failed = False

    def init(self) -> None:
        if self.one_transaction:
            self._connection = self._connect()
            self._transaction_failed = False

    def close(self) -> None:
        if self._connection is None:
            return
        try:
            if self._transaction_failed:
                self._connection.rollback()
            else:
                self._connection.commit()
        finally:
            self._connection.close()
            self._connection = None

    def deploy(self, source: str) -> OperationStatus:
        if self.one_transaction:
            try:
                if self._connection is None:
                    return OpFailure("No active connection for one_transaction mode.")
                with self._connection.cursor() as cursor:
                    cursor.execute(source.encode("utf-8"))
            except psycopg.Error as error:
                self._transaction_failed = True
                return OpFailure(str(error))
            return OpSuccess()
        else:
            try:
                with self._connect() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute(source.encode("utf-8"))
            except psycopg.Error as error:
                return OpFailure(str(error))

            return OpSuccess()

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
        return psycopg.connect(**connection_parameters)
