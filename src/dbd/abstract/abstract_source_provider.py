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

from abc import ABC, abstractmethod

from dbd.core.configurable import Configurable


class AbstractSourceProvider(Configurable, ABC):

    _sources_list: list[str] | None = None

    @abstractmethod
    def _get_sources_list(self) -> list[str]:
        """Return a list of source names."""

    @abstractmethod
    def _get_source(self, source_name: str) -> str:
        """Return the source for the given source name."""

    def get_sources_list(self) -> list[str]:
        """Return a list of source names."""
        result: list[str] = self._get_sources_list()
        self._sources_list = result
        return result

    def get_source(self, source_name: str) -> str:
        """Return the source for the given source name."""
        if self._sources_list is None:
            _sources = self.get_sources_list()
        else:
            _sources = self._sources_list

        if source_name not in _sources:
            raise ValueError(f"Source '{source_name}' does not exist.")

        return self._get_source(source_name)
