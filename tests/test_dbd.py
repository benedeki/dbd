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

import sys

import pytest

from dbd.dbd import Action, _load_parameters


def test_load_parameters_reads_action_and_config_path(tmp_path, monkeypatch):
    config_path = tmp_path / "config with spaces.json"
    config_path.write_text('{"name": "example"}', encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["dbd", "install", str(config_path)])

    action, config = _load_parameters()

    assert action is Action.INSTALL
    assert config._data == {"name": "example"}


@pytest.mark.parametrize("action", ["deploy", ""])
def test_load_parameters_rejects_unknown_action(action, tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["dbd", action, str(config_path)])

    with pytest.raises(ValueError):
        _load_parameters()
