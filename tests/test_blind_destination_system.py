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

from dbd.implementations.blind.destination_system import DestinationSystem
from dbd.core.operation_status import OpSuccess
from dbd.core.simple_config import SimpleConfig


def test_deploy_prints_source_and_returns_success(capsys):
    source = "CREATE TABLE example (id integer);"

    result = DestinationSystem(SimpleConfig({})).deploy(source)

    assert result == OpSuccess()
    assert capsys.readouterr().out == f"\n{'=' * 80}\n\n{source}\n"
