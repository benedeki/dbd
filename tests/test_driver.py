#
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
#
from unittest.mock import Mock

import pytest

from dbd.core.config import Config
from dbd.core.driver import Driver
from dbd.core.operation_status import OpFailure, OpSuccess, OpWarning


def make_driver(record_keeper=None, source_provider=None, destination_system=None):
    return Driver(
        Config({}),
        record_keeper or Mock(),
        source_provider or Mock(),
        destination_system or Mock(),
    )


def test_compute_hash_uses_git_blob_hash_format():
    assert Driver._compute_hash("hello") == "b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0"


def test_map_source_variables_returns_source_when_no_mappings():
    driver = make_driver()

    assert driver._map_source_variables("SELECT '{{name}}'") == "SELECT '{{name}}'"


def test_install_records_successful_deployment():
    record_keeper = Mock()
    record_keeper.check_source_for_deploy.return_value = False
    source_provider = Mock()
    source_provider.get_sources_list.return_value = ["users"]
    source_provider.get_source.return_value = "CREATE TABLE users;"
    destination_system = Mock()
    destination_system.deploy.return_value = OpSuccess()
    driver = make_driver(record_keeper, source_provider, destination_system)

    warnings = driver.install()

    source_hash = Driver._compute_hash("CREATE TABLE users;")
    assert warnings == {}
    record_keeper.start_session.assert_called_once_with(driver.config)
    destination_system.deploy.assert_called_once_with("CREATE TABLE users;")
    record_keeper.record.assert_called_once_with("users", source_hash)
    record_keeper.end_session.assert_called_once_with({})


@pytest.mark.parametrize(
    ("status", "expected_warnings"),
    [
        (OpWarning("applied with caution"), {"users": "applied with caution"}),
        (OpFailure("deployment failed"), {}),
    ],
)
def test_install_handles_deployment_statuses(status, expected_warnings):
    record_keeper = Mock()
    record_keeper.check_source_for_deploy.return_value = False
    source_provider = Mock()
    source_provider.get_sources_list.return_value = ["users"]
    source_provider.get_source.return_value = "CREATE TABLE users;"
    destination_system = Mock()
    destination_system.deploy.return_value = status
    driver = make_driver(record_keeper, source_provider, destination_system)

    warnings = driver.install()

    assert warnings == expected_warnings
    if isinstance(status, OpWarning):
        record_keeper.record.assert_called_once()
    else:
        record_keeper.fail_session.assert_called_once_with(
            "users",
            Driver._compute_hash("CREATE TABLE users;"),
            "deployment failed",
        )
    record_keeper.end_session.assert_called_once_with(expected_warnings)


def test_install_skips_sources_that_do_not_need_deployment():
    record_keeper = Mock()
    record_keeper.check_source_for_deploy.return_value = True
    source_provider = Mock()
    source_provider.get_sources_list.return_value = ["users"]
    source_provider.get_source.return_value = "CREATE TABLE users;"
    destination_system = Mock()
    driver = make_driver(record_keeper, source_provider, destination_system)

    assert driver.install() == {}

    destination_system.deploy.assert_not_called()
    record_keeper.record.assert_not_called()
    record_keeper.fail_session.assert_not_called()
    record_keeper.end_session.assert_called_once_with({})
