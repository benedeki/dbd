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

from dbd.abstract.abstract_source_provider import AbstractSourceProvider


class SourceProvider(AbstractSourceProvider):
    def _get_source(self, source_name: str) -> str:
        raise NotImplementedError("This source provider does not provide any sources.")

    def _get_sources_list(self) -> list[str]:
        return []
