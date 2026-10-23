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

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from psycopg import errors

from dbd.core.simple_config import SimpleConfig
from dbd.implementations.postgres import record_keeper as postgres_record_keeper
from dbd.implementations.postgres.record_keeper import RecordKeeper


@pytest.fixture
def config() -> SimpleConfig:
    return SimpleConfig(
        {
            "connection": {
                "host": "localhost",
                "port": 5432,
                "dbname": "dbd",
                "user": "dbd-user",
                "password": "secret",
                "sslmode": "prefer",
                "sslcert": "",
                "connect_timeout": 10,
            },
            "one_transaction": True,
            "group_id": None,
            "auto_deploy": True,
            "source_code_location_override": None,
        }
    )


def test_connection_is_created_lazily_and_reused(config: SimpleConfig):
    record_keeper = RecordKeeper(config)
    connection = MagicMock()

    with patch.object(record_keeper, "_connect", return_value=connection) as connect:
        assert record_keeper._connection is connection
        assert record_keeper._connection is connection

    connect.assert_called_once_with()


def test_start_and_end_session_use_one_transaction_connection(config: SimpleConfig):
    record_keeper = RecordKeeper(config)
    record_keeper._version_checked = True
    connection = MagicMock()
    session_id = uuid4()

    with (
        patch.object(record_keeper, "_connect", return_value=connection),
        patch.object(
            postgres_record_keeper._DBDNewSession,
            "execute",
            return_value=SimpleNamespace(session_id=session_id),
        ) as new_session,
        patch.object(
            postgres_record_keeper._DBDRecordSessionSources,
            "execute",
            return_value={},
        ) as record_sources,
        patch.object(postgres_record_keeper._DBDCloseSession, "execute") as close_session,
    ):
        record_keeper.start_session()
        record_keeper.end_session({"users": "warning"})

    new_session.assert_called_once_with(connection, None)
    record_sources.assert_called_once_with(connection, session_id, {}, [])
    close_session.assert_called_once_with(
        connection,
        session_id,
        True,
        {"warnings": {"users": "warning"}},
    )
    connection.commit.assert_called_once_with()
    connection.close.assert_called_once_with()
    assert not record_keeper.session_started


def test_record_and_checked_sources_are_buffered_in_one_transaction(config: SimpleConfig):
    record_keeper = RecordKeeper(config)
    record_keeper._session_id = uuid4()

    record_keeper.record_deploy("users.sql", "hash")
    record_keeper.source_checked("views.sql")

    assert record_keeper._deployed_sources == {"users.sql": "hash"}
    assert record_keeper._checked_sources == ["views.sql"]


def test_get_source_hash_loads_sources_once_and_returns_requested_hash(config: SimpleConfig):
    config = SimpleConfig({**config._data, "one_transaction": False})
    record_keeper = RecordKeeper(config)
    record_keeper._session_id = uuid4()
    connection = MagicMock()
    source_hashes = {"users.sql": "hash"}

    with (
        patch.object(record_keeper, "_connect", return_value=connection),
        patch.object(
            postgres_record_keeper._DBDGetSourcesWithHashes,
            "execute",
            return_value=source_hashes,
        ) as get_sources,
    ):
        assert record_keeper.get_source_hash("users.sql") == "hash"
        assert record_keeper.get_source_hash("missing.sql") is None

    get_sources.assert_called_once_with(connection.__enter__(), None)


def test_get_sources_with_hashes_maps_rows_to_source_hashes():
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        SimpleNamespace(source_name="users.sql", source_hash="users-hash"),
        SimpleNamespace(source_name="views.sql", source_hash="views-hash"),
    ]
    result = postgres_record_keeper._DBDGetSourcesWithHashes.execute(
        connection,
        None,
    )

    assert result == {
        "users.sql": "users-hash",
        "views.sql": "views-hash",
    }
    cursor.execute.assert_called_once()
    assert cursor.execute.call_args.args[1] == {"i_group_id": None}


def test_session_methods_require_an_active_session(config: SimpleConfig):
    record_keeper = RecordKeeper(config)

    for method, args in (
        (record_keeper.end_session, ({},)),
        (record_keeper.fail_session, ("users.sql", "hash", "error")),
        (record_keeper.get_source_hash, ("users.sql",)),
        (record_keeper.record_deploy, ("users.sql", "hash")),
        (record_keeper.source_checked, ("users.sql",)),
    ):
        with pytest.raises(RuntimeError, match="Session has not been started"):
            method(*args)


def test_start_session_rejects_an_existing_session(config: SimpleConfig):
    record_keeper = RecordKeeper(config)
    record_keeper._session_id = uuid4()

    with pytest.raises(RuntimeError, match="Session has already been started"):
        record_keeper.start_session()


def test_fail_session_raises_deployment_error(config: SimpleConfig):
    record_keeper = RecordKeeper(config)
    session_id = uuid4()
    record_keeper._session_id = session_id
    record_keeper._e_connection = MagicMock()
    with patch.object(postgres_record_keeper._DBDCloseSession, "execute"):
        with pytest.raises(RuntimeError, match="deployment failed"):
            record_keeper.fail_session("users.sql", "hash", "deployment failed")


def test_individual_transaction_session_operations_use_new_connections(config: SimpleConfig):
    config = SimpleConfig({**config._data, "one_transaction": False})
    record_keeper = RecordKeeper(config)
    record_keeper._version_checked = True
    connection = MagicMock()
    connection.__enter__.return_value = connection
    session_id = uuid4()
    sources = {"users.sql": "hash"}

    with (
        patch.object(record_keeper, "_connect", return_value=connection) as connect,
        patch.object(
            postgres_record_keeper._DBDNewSession,
            "execute",
            return_value=SimpleNamespace(session_id=session_id),
        ),
        patch.object(
            postgres_record_keeper._DBDGetSourcesWithHashes,
            "execute",
            return_value=sources,
        ),
        patch.object(postgres_record_keeper._DBDRecordSourceDeployed, "execute") as record_source,
        patch.object(postgres_record_keeper._DBDSourceChecked, "execute") as source_checked,
        patch.object(postgres_record_keeper._DBDCloseSession, "execute") as close_session,
    ):
        record_keeper.start_session()
        record_keeper.record_deploy("users.sql", "hash")
        record_keeper.source_checked("views.sql")
        assert record_keeper.get_source_hash("users.sql") == "hash"
        record_keeper.end_session({})

        record_keeper._session_id = session_id
        with pytest.raises(RuntimeError, match="deployment failed"):
            record_keeper.fail_session("users.sql", "hash", "deployment failed")

    assert connect.call_count == 6
    record_source.assert_called_once_with(connection, session_id, "users.sql", "hash")
    source_checked.assert_called_once_with(connection, session_id, "views.sql")
    assert close_session.call_count == 2


def test_check_version_skips_redeploy_when_current(config: SimpleConfig):
    record_keeper = RecordKeeper(config)
    connection = MagicMock()

    with (
        patch.object(record_keeper, "_connect", return_value=connection),
        patch.object(
            postgres_record_keeper._DBDVersion,
            "execute",
            return_value=SimpleNamespace(version_number=postgres_record_keeper.CURRENT_VERSION),
        ),
        patch.object(record_keeper, "_redeploy") as redeploy,
    ):
        record_keeper._check_version()

    redeploy.assert_not_called()
    assert record_keeper._version_checked


def test_check_version_rejects_mismatch_when_auto_deploy_disabled(config: SimpleConfig):
    config = SimpleConfig({**config._data, "auto_deploy": False})
    record_keeper = RecordKeeper(config)
    connection = MagicMock()

    with (
        patch.object(record_keeper, "_connect", return_value=connection),
        patch.object(
            postgres_record_keeper._DBDVersion,
            "execute",
            return_value=SimpleNamespace(version_number=postgres_record_keeper.CURRENT_VERSION - 1),
        ),
    ):
        with pytest.raises(RuntimeError, match="DBD version mismatch or not deployed"):
            record_keeper._check_version()


def test_check_version_redeploys_when_function_is_missing(config: SimpleConfig):
    record_keeper = RecordKeeper(config)
    connection = MagicMock()

    with (
        patch.object(record_keeper, "_connect", return_value=connection),
        patch.object(
            postgres_record_keeper._DBDVersion,
            "execute",
            side_effect=errors.UndefinedFunction("missing"),
        ),
        patch.object(record_keeper, "_redeploy") as redeploy,
    ):
        record_keeper._check_version()

    redeploy.assert_called_once_with()
    assert record_keeper._version_checked


def test_redeploy_builds_driver_from_override_path(config: SimpleConfig):
    override_path = Path("dbd-sources").resolve()
    config = SimpleConfig({**config._data, "source_code_location_override": str(override_path)})
    record_keeper = RecordKeeper(config)
    blind_record_keeper = MagicMock()
    source_provider = MagicMock()
    destination_system = MagicMock()
    driver = MagicMock()

    with (
        patch.object(postgres_record_keeper, "BlindRecordKeeper", return_value=blind_record_keeper),
        patch.object(
            postgres_record_keeper,
            "FileSourceProvider",
            return_value=source_provider,
        ) as source_provider_type,
        patch.object(postgres_record_keeper, "PostgresDestinationSystem", return_value=destination_system),
        patch.object(postgres_record_keeper, "Driver", return_value=driver) as driver_type,
    ):
        record_keeper._redeploy()

    driver_type.assert_called_once()
    assert driver_type.call_args.args[1:] == (
        blind_record_keeper,
        source_provider,
        destination_system,
    )
    source_provider_config = source_provider_type.call_args.args[0]
    assert Path(source_provider_config.get_as_str("path")).resolve() == override_path
    driver.install.assert_called_once_with()


def test_redeploy_uses_bundled_database_scripts_by_default(config: SimpleConfig):
    record_keeper = RecordKeeper(config)
    source_provider = MagicMock()
    driver = MagicMock()

    with (
        patch.object(postgres_record_keeper, "BlindRecordKeeper"),
        patch.object(postgres_record_keeper, "FileSourceProvider", return_value=source_provider) as source_type,
        patch.object(postgres_record_keeper, "PostgresDestinationSystem"),
        patch.object(postgres_record_keeper, "Driver", return_value=driver),
    ):
        record_keeper._redeploy()

    source_path = source_type.call_args.args[0].get_as_str("path")
    assert Path(source_path).name == "dbd"


def test_database_helpers_return_rows_for_all_result_types():
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    session_id = uuid4()

    cursor.fetchone.side_effect = [
        SimpleNamespace(first_deployment_key_session=session_id),
        SimpleNamespace(first_deployment_key_session=session_id),
        SimpleNamespace(
            sources_deployed=1,
            sources_redeployed=0,
            sources_checked=1,
            checked_sources_not_found=0,
        ),
        SimpleNamespace(group_id="group", session_start=None, session_end=None),
    ]

    record_source = postgres_record_keeper._DBDRecordSourceDeployed.execute(
        connection, session_id, "users.sql", "hash"
    )
    source_checked = postgres_record_keeper._DBDSourceChecked.execute(
        connection, session_id, "users.sql"
    )
    session_sources = postgres_record_keeper._DBDRecordSessionSources.execute(
        connection, session_id, {"users.sql": "hash"}, ["views.sql"]
    )
    closed_session = postgres_record_keeper._DBDCloseSession.execute(
        connection, session_id, True, {}
    )

    assert record_source.first_deployment_key_session == session_id
    assert source_checked.first_deployment_key_session == session_id
    assert session_sources.sources_deployed == 1
    assert closed_session.group_id == "group"


@pytest.mark.parametrize(
    ("helper", "row"),
    [
        (
            postgres_record_keeper._DBDVersion,
            SimpleNamespace(version_number=1),
        ),
        (
            postgres_record_keeper._DBDNewSession,
            SimpleNamespace(session_id=uuid4()),
        ),
    ],
)
def test_database_helpers_return_rows(helper, row):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = row

    if helper is postgres_record_keeper._DBDVersion:
        result = helper.execute(connection)
        assert result.version_number == row.version_number
    else:
        result = helper.execute(connection, None)
        assert result.session_id == row.session_id

    cursor.execute.assert_called_once()


@pytest.mark.parametrize(
    "helper_call",
    [
        lambda connection: postgres_record_keeper._DBDVersion.execute(connection),
        lambda connection: postgres_record_keeper._DBDNewSession.execute(connection, None),
        lambda connection: postgres_record_keeper._DBDRecordSourceDeployed.execute(
            connection, uuid4(), "users.sql", "hash"
        ),
        lambda connection: postgres_record_keeper._DBDSourceChecked.execute(
            connection, uuid4(), "users.sql"
        ),
        lambda connection: postgres_record_keeper._DBDCloseSession.execute(
            connection, uuid4(), True, {}
        ),
    ],
)
def test_database_helpers_raise_when_database_returns_no_row(helper_call):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []

    with pytest.raises(RuntimeError, match="returned no"):
        helper_call(connection)
