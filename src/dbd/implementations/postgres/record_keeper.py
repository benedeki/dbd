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

import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg import errors
from psycopg.rows import class_row
from psycopg.types.json import Jsonb

from dbd.abstract.abstract_record_keeper import AbstractRecordKeeper
from dbd.core.driver import Driver
from dbd.core.simple_config import SimpleConfig
from dbd.implementations.blind.record_keeper import RecordKeeper as BlindRecordKeeper
from dbd.implementations.file.source_provider import SourceProvider as FileSourceProvider
from dbd.implementations.postgres._postgres_connector import _PostgresConnector
from dbd.implementations.postgres.destination_system import DestinationSystem as PostgresDestinationSystem

CURRENT_VERSION = 1

class RecordKeeper(AbstractRecordKeeper, _PostgresConnector):
    @property
    def session_started(self) -> bool:
        return self._session_id is not None

    _session_id: uuid.UUID | None = None
    _version_checked: bool = False
    _group_id: str
    _e_connection: psycopg.Connection | None = None
    _sources: dict[str, str] | None = None

    _deployed_sources: dict[str, str]
    _checked_sources: list[str]

    @property
    def _connection(self) -> psycopg.Connection:
        if self._e_connection is None:
            connection = self._connect()
            self._e_connection = connection
            return connection
        else:
            return self._e_connection


    def __init__(self, config: SimpleConfig):
        connection_config = config.get_as_config("connection")
        _one_transaction = config.get_as_bool("one_transaction", True)
        AbstractRecordKeeper.__init__(self, config)
        _PostgresConnector.__init__(self, connection_config, _one_transaction)
        self._group_id = config.get_as_str("group_id", "")
        self._auto_deploy = config.get_as_bool("auto_deploy", True)
        self._source_code_location_override = config.get_as_str_optional("source_code_location_override")
        self._reset()


    def start_session(self) -> None:
        # Implement the logic to start a session with the record keeper
        if self.session_started:
            raise RuntimeError("Session has already been started.")

        if not self._version_checked:
            self._check_version()

        if self.one_transaction:
            self._session_id = _DBDNewSession.execute(self._connection, self._group_id).session_id
        else:
            with self._connect() as conn:
                self._session_id = _DBDNewSession.execute(conn, self._group_id).session_id


    def end_session(self, warnings: dict[str, str]) -> None:
        # Implement the logic to end the session with the record keeper
        if self._session_id is None:
            raise RuntimeError("Session has not been started.")
        if warnings:
            logs = {"warnings": warnings}
        else:
            logs = {}
        if self.one_transaction:
            try:
                _DBDRecordSessionSources.execute(
                    self._connection,
                    self._session_id,
                    self._deployed_sources,
                    self._checked_sources
                )
                _DBDCloseSession.execute(self._connection, self._session_id, True, logs)
                self._connection.commit()
            finally:
                self._reset()
        else:
            with self._connect() as conn:
                _DBDCloseSession.execute(conn, self._session_id, True, logs)
            self._reset()


    def fail_session(self, source_name: str, source_hash: str, error_message: str) -> None:
        if self._session_id is None:
            raise RuntimeError("Session has not been started.")
        logs = {
            "error": {
                "source_name": source_name,
                "source_hash": source_hash,
                "message": error_message
            }
        }
        if self.one_transaction:
            try:
                _DBDCloseSession.execute(self._connection, self._session_id, False, logs)
                self._connection.commit()
            finally:
                self._reset()
        else:
            with self._connect() as conn:
                _DBDCloseSession.execute(conn, self._session_id, False, logs)
            self._reset()
        super().fail_session(source_name, source_hash, error_message)



    def get_source_hash(self, source_name: str) -> str | None:
        # Implement the logic to get the hash of a given source
        if self._session_id is None:
            raise RuntimeError("Session has not been started.")
        if self._sources is None:
            if self.one_transaction:
                sources = _DBDGetSourcesWithHashes.execute(self._connection, self._group_id)
                self._sources = sources
            else:
                with self._connect() as conn:
                    sources = _DBDGetSourcesWithHashes.execute(conn, self._group_id)
                    self._sources = sources
        else:
            sources = self._sources
        return sources.get(source_name)


    def record_deploy(self, source_name: str, source_hash: str) -> None:
        # Implement the logic to record the deployment event
        if self._session_id is None:
            raise RuntimeError("Session has not been started.")

        if self.one_transaction:
            self._deployed_sources[source_name] = source_hash
        else:
            with self._connect() as conn:
                _DBDRecordSourceDeployed.execute(conn, self._session_id, source_name, source_hash)

    def source_checked(self, source_name: str) -> None:
        if self._session_id is None:
            raise RuntimeError("Session has not been started.")

        if self.one_transaction:
            self._checked_sources.append(source_name)
        else:
            with self._connect() as conn:
                _DBDSourceChecked.execute(conn, self._session_id, source_name)


    def _check_version(self) -> None:
        redeploy = False
        with self._connect() as conn:
            try:
                deployed_version = _DBDVersion.execute(conn).version_number
                redeploy = deployed_version < CURRENT_VERSION
                # TODO log a warning if deployed_version > CURRENT_VERSION
            except (errors.UndefinedFunction, errors.InvalidSchemaName):
                redeploy = True  # dbd schema/function not deployed yet

        if redeploy:
            if not self._auto_deploy:
                raise RuntimeError(
                    f"DBD version mismatch or not deployed. Expected version {CURRENT_VERSION}. "
                    "Please redeploy the DBD schema and functions."
                )
            self._redeploy()
        self._version_checked = True

    def _redeploy(self) -> None:
        driver_config: SimpleConfig =  SimpleConfig(
            {
                "mappings": {
                    "INSTALLING_USER": self._user,
                    "VERSION_NUMBER": str(CURRENT_VERSION)
                }
            }
        )

        record_keeper_config = SimpleConfig({})
        record_keeper = BlindRecordKeeper(record_keeper_config)

        if self._source_code_location_override:
            source_path = self._source_code_location_override
        else:
            script_dir = Path(__file__).resolve().parent
            dbd_dir = script_dir / "dbd"
            source_path = str(dbd_dir)
        source_provider_config = SimpleConfig(
            {
                "path": source_path,
                "file_masks": ["*.sql", "*.ddl"],
            }
        )
        source_provider = FileSourceProvider(source_provider_config)

        destination_provider_config = SimpleConfig(
            {
                "one_transaction": True,
                "connection": self.config.get_as_dict("connection"),
            }
        )
        destination_system = PostgresDestinationSystem(destination_provider_config)

        redeploy_driver = Driver(driver_config, record_keeper, source_provider, destination_system)
        redeploy_driver.install()

    def _reset(self) -> None:
        self._session_id = None
        self._sources = None
        self._deployed_sources = {}
        self._checked_sources = []
        if self._e_connection is not None:
            self._e_connection.close()
            self._e_connection = None


@dataclass(frozen=True)
class _DBDVersion:
    version_number: int

    @classmethod
    def execute(cls, conn: psycopg.Connection) -> _DBDVersion:
        with conn.cursor(row_factory=class_row(_DBDVersion)) as cur:
            cur.execute("SELECT V.version_number FROM dbd.version() AS V")
            result = cur.fetchone()
            if result is None:
                raise RuntimeError("dbd.version returned no rows (should never happen).")
            return result


@dataclass(frozen=True)
class _DBDNewSession:
    session_id: uuid.UUID

    @classmethod
    def execute(cls, conn: psycopg.Connection, group_id: str) -> _DBDNewSession:
        with conn.cursor(row_factory=class_row(_DBDNewSession)) as cur:
            cur.execute("""
                SELECT NS.session_id
                FROM dbd.new_session(%(i_group_id)s) AS NS
                """,
                {"i_group_id": group_id}
            )
            result = cur.fetchone()
            if result is None:
                raise RuntimeError("dbd.new_session returned no rows (should never happen).")
            return result


@dataclass(frozen=True)
class _DBDRecordSourceDeployed:
    first_deployment_session_id: uuid.UUID

    @classmethod
    def execute(cls, conn: psycopg.Connection,
                session_id: uuid.UUID,
                source_name: str,
                source_hash: str) -> _DBDRecordSourceDeployed:
        with conn.cursor(row_factory=class_row(_DBDRecordSourceDeployed)) as cur:
            cur.execute(
                """
                SELECT RS.first_deployment_session_id
                FROM dbd.record_source_deployed(%(session_id)s, %(source_name)s, %(source_hash)s) AS RS
                """,
                {"session_id": session_id, "source_name": source_name, "source_hash": source_hash}
            )
            result = cur.fetchone()
            if result is None:
                raise RuntimeError("dbd.record_source_deployed returned no rows (should never happen).")
            return result


@dataclass(frozen=True)
class _DBDSourceChecked:
    first_deployment_session_id: uuid.UUID

    @classmethod
    def execute(cls, conn: psycopg.Connection,
                session_id: uuid.UUID,
                source_name: str) -> _DBDSourceChecked:
        with conn.cursor(row_factory=class_row(_DBDSourceChecked)) as cur:
            cur.execute(
                """
                SELECT SC.first_deployment_session_id
                FROM dbd.record_source_checked(%(session_id)s, %(source_name)s) AS SC
                """,
                {"session_id": session_id, "source_name": source_name}
            )
            result = cur.fetchone()
            if result is None:
                raise RuntimeError("dbd.record_source_checked returned no rows (should never happen).")
            return result


@dataclass(frozen=True)
class _DBDGetSourcesWithHashes:
    source_name: str
    source_hash: str

    @classmethod
    def execute(cls, conn: psycopg.Connection, group_id: str) -> dict[str, str]:
        with conn.cursor(row_factory=class_row(_DBDGetSourcesWithHashes)) as cur:
            cur.execute(
                """
                SELECT RSS.source_name, RSS.source_hash
                FROM dbd.get_sources_with_hashes(%(i_group_id)s) AS RSS
                """,
                {
                    "i_group_id": group_id
                },
            )
            data = cur.fetchall()
            result = {}
            for row in data:
                result[row.source_name] = row.source_hash
            return result


@dataclass(frozen=True)
class _DBDRecordSessionSources:
    sources_deployed: int
    sources_redeployed: int
    sources_checked: int
    checked_sources_not_found: int

    @classmethod
    def execute(cls, conn: psycopg.Connection,
                session_id: uuid.UUID,
                deployed_sources: dict[str, str],
                checked_sources: list[str]
                ) -> _DBDRecordSessionSources:
        deployed_sources_names = list(deployed_sources)
        deployed_sources_hashes = list(deployed_sources.values())
        with conn.cursor(row_factory=class_row(_DBDRecordSessionSources)) as cur:
            cur.execute(
                """
                SELECT RSS.sources_deployed, RSS.sources_redeployed, RSS.sources_checked, RSS.checked_sources_not_found
                FROM dbd.record_session_sources(
                    %(session_id)s,
                    %(deployed_sources)s::text[],
                    %(deployed_hashes)s::text[],
                    %(checked_sources)s::text[]
                              ) AS RSS
                """,
                {
                    "session_id": session_id,
                    "deployed_sources": deployed_sources_names,
                    "deployed_hashes": deployed_sources_hashes,
                    "checked_sources": checked_sources,
                }
            )
            result = cur.fetchone()
            if result is None:
                raise RuntimeError("dbd.record_session_sources returned no rows (should never happen).")
            return result


@dataclass(frozen=True)
class _DBDCloseSession:
    group_id: str
    session_start: datetime
    session_end: datetime

    @classmethod
    def execute(cls, conn: psycopg.Connection,
                session_id: uuid.UUID,
                ended_with_success: bool,
                session_log: dict) -> _DBDCloseSession:
        with conn.cursor(row_factory=class_row(_DBDCloseSession)) as cur:
            cur.execute(
                """
                SELECT CS.group_id, CS.session_start, CS.session_end
                FROM dbd.close_session(%(session_id)s, %(success)s, %(log)s) CS
                """,
                {
                    "session_id": session_id,
                    "success": ended_with_success,
                    "log": Jsonb(session_log),
                },
            )
            result = cur.fetchone()
            if result is None:
                raise RuntimeError("dbd.close_session returned no row (should never happen).")
            return result
