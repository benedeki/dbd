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

import psycopg

from dbd.abstract.abstract_destination_system import AbstractDestinationSystem
from dbd.core.operation_status import OperationStatus, OpFailure, OpSuccess
from dbd.core.simple_config import SimpleConfig
from dbd.implementations.postgres._postgres_connector import _PostgresConnector


class DestinationSystem(AbstractDestinationSystem, _PostgresConnector):
    _connection: psycopg.Connection | None = None

    def __init__(self, config: SimpleConfig):
        super().__init__(config)
        connection_config = config.get_as_config("connection")
        _one_transaction = config.get_as_bool("one_transaction", True)
        AbstractDestinationSystem.__init__(self, config)
        _PostgresConnector.__init__(self, connection_config, _one_transaction)

    def init(self) -> None:
        if self.one_transaction:
            self._connection = self._connect()
            self._transaction_failed = False

    def close(self, was_successful: bool) -> None:
        if self._connection is None:
            return
        try:
            if self._transaction_failed or not was_successful:
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
