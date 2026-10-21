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

import pytest

from dbd.core.simple_config import SimpleConfig
from dbd.implementations.blind.source_provider import SourceProvider


def test_get_sources_list_is_empty():
    provider = SourceProvider(SimpleConfig({}))

    assert provider.get_sources_list() == []


def test_get_source_rejects_every_source_name():
    provider = SourceProvider(SimpleConfig({}))

    with pytest.raises(ValueError, match="Source 'source.sql' does not exist."):
        provider.get_source("source.sql")


def test_get_source_is_not_implemented_for_a_listed_source():
    provider = SourceProvider(SimpleConfig({}))
    provider._sources_list = ["source.sql"]

    with pytest.raises(NotImplementedError, match="does not provide any sources"):
        provider.get_source("source.sql")
