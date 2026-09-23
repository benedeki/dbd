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

import hashlib
import re

from dbd.abstract.abstract_destination_system import AbstractDestinationSystem
from dbd.abstract.abstract_record_keeper import AbstractRecordKeeper
from dbd.abstract.abstract_source_provider import AbstractSourceProvider
from dbd.core.config import Config
from dbd.core.configurable import Configurable
from dbd.core.operation_status import OpFailure, OpSuccess, OpWarning


class Driver(Configurable):
    """The main execution class."""

    def __init__(self,
                 config: Config,
                 record_keeper: AbstractRecordKeeper,
                 source_provider: AbstractSourceProvider,
                 destination_system: AbstractDestinationSystem):
        super().__init__(config)
        self._record_keeper = record_keeper
        self._source_provider = source_provider
        self._destination_system = destination_system
        self._mappings = self._extract_mappings()

    def install(self) -> dict[str, str]:
        """Read and process the sources and apply them to the destination system."""
        self._record_keeper.start_session(self.config)
        warnings = {}
        for source_name in self._source_provider.get_sources_list():
            source_content = self._map_source_variables(self._source_provider.get_source(source_name))
            source_hash = self._compute_hash(source_content)
            if not self._record_keeper.check_source_for_deploy(source_name, source_hash):
                result = self._destination_system.deploy(source_content)
                match result:
                    case OpSuccess():
                        self._record_keeper.record(source_name, source_hash)
                    case OpWarning(msg):
                        warnings[source_name] = msg
                        self._record_keeper.record(source_name, source_hash)
                    case OpFailure(msg):
                        self._record_keeper.fail_session(source_name, source_hash, msg)

        self._record_keeper.end_session(warnings)
        return warnings

    @staticmethod
    def _compute_hash(source: str) -> str:
        """Compute a hash for the given source string, same as git does for blob objects."""
        data = source.encode("utf-8")
        header = f"blob {len(data)}\0".encode()
        return hashlib.sha1(header + data).hexdigest()

    def _extract_mappings(self) -> dict[str, str]:
        """Expand the mapping keys to include the start and end markers."""
        mapping: dict[str, str] = self.config.get_as_dict("mappings", {})
        start_marker = "{{"
        end_marker = "}}"
        return {f"{start_marker}{k}{end_marker}": v for k, v in mapping.items()}

    def _map_source_variables(self, source: str) -> str:
        """Map the placeholders in the source string."""
        if not self._mappings:
            return source
        # Sort by key length descending so longer keys match before shorter ones
        # that might be substrings of them (e.g. "cat" vs "category")
        pattern = re.compile(
            "|".join(re.escape(k) for k in sorted(self._mappings, key=len, reverse=True))
        )
        return pattern.sub(lambda m: self._mappings[m.group(0)], source)
