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
import sys

import pytest

from dbd.abstract.abstract_destination_system import AbstractDestinationSystem
from dbd.abstract.abstract_record_keeper import AbstractRecordKeeper
from dbd.abstract.abstract_source_provider import AbstractSourceProvider
from dbd.core.expandable_config import ExpandableConfig
from dbd.dbd import Action, _load_classes, _load_parameters
from dbd.implementations.blind.destination_system import DestinationSystem
from dbd.implementations.blind.record_keeper import RecordKeeper
from dbd.implementations.blind.secret_reader import SecretReader
from dbd.implementations.file.source_provider import SourceProvider


def test_load_parameters_reads_action_and_config_path(tmp_path, monkeypatch):
    config_path = tmp_path / "config with spaces.json"
    config_path.write_text('{"name": "example"}', encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["dbd", "install", str(config_path)])

    action, config_file, cli_parameters = _load_parameters()

    assert action is Action.INSTALL
    assert config_file == str(config_path)
    assert cli_parameters == {}


@pytest.mark.parametrize("action", ["deploy", ""])
def test_load_parameters_rejects_unknown_action(action, tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["dbd", action, str(config_path)])

    with pytest.raises(ValueError):
        _load_parameters()


def test_load_classes_imports_configured_secret_reader(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "secret_reader": {"type": "blind", "config": {}},
                "record_keeper": {"type": "blind", "config": {}},
                "source_provider": {
                    "type": "file",
                    "config": {
                        "path": str(tmp_path),
                        "file_masks": ["*.sql"],
                    },
                },
                "destination_system": {"type": "blind", "config": {}},
            }
        ),
        encoding="utf-8",
    )
    config = ExpandableConfig(str(config_path), {})
    expanded_with = []

    monkeypatch.setattr(
        config,
        "expand",
        lambda secret_reader=None, branch="": expanded_with.append(secret_reader),
    )

    record_keeper, source_provider, destination_system = _load_classes(config)

    assert len(expanded_with) == 1
    assert isinstance(expanded_with[0], SecretReader)
    assert isinstance(record_keeper, AbstractRecordKeeper)
    assert isinstance(record_keeper, RecordKeeper)
    assert isinstance(source_provider, AbstractSourceProvider)
    assert isinstance(source_provider, SourceProvider)
    assert isinstance(destination_system, AbstractDestinationSystem)
    assert isinstance(destination_system, DestinationSystem)


def test_load_classes_honors_module_and_class_overrides(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "secret_reader": {
                    "type": "blind",
                    "config": {},
                    "source_file_override": "secret_reader",
                    "class_override": "SecretReader",
                },
                "record_keeper": {
                    "type": "blind",
                    "config": {},
                    "source_file_override": "record_keeper",
                    "class_override": "RecordKeeper",
                },
                "source_provider": {
                    "type": "file",
                    "config": {
                        "path": str(tmp_path),
                        "file_masks": ["*.sql"],
                    },
                    "source_file_override": "source_provider",
                    "class_override": "SourceProvider",
                },
                "destination_system": {
                    "type": "blind",
                    "config": {},
                    "source_file_override": "destination_system",
                    "class_override": "DestinationSystem",
                },
            }
        ),
        encoding="utf-8",
    )
    config = ExpandableConfig(str(config_path), {})

    record_keeper, source_provider, destination_system = _load_classes(config)

    assert isinstance(record_keeper, RecordKeeper)
    assert isinstance(source_provider, SourceProvider)
    assert isinstance(destination_system, DestinationSystem)
