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

from dbd.core.simple_config import SimpleConfig
from dbd.implementations.blind.record_keeper import RecordKeeper


def test_record_keeper_methods_are_no_ops():
    record_keeper = RecordKeeper(SimpleConfig({}))

    assert record_keeper.start_session() is None
    assert record_keeper.end_session({"warning": "ignored"}) is None
    assert record_keeper.get_source_hash("source.sql") is None
    assert record_keeper.record_deploy("source.sql", "hash") is None
    assert record_keeper.source_checked("source.sql") is None
