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

from dbd.abstract.abstract_source_provider import AbstractSourceProvider
from dbd.core.config import Config


class SourceProvider(AbstractSourceProvider):

    @property
    def source_dir(self) -> Path:
        return self._source_dir

    @property
    def source_file_masks(self) -> list[str]:
        return self._source_file_masks

    def __init__(self, config: Config):
        super().__init__(config)
        self._source_dir = Path(self.config.get_as_str("path"))
        self._source_file_masks = self.config.get_as_list("file_masks", ["*"])

    def _get_sources_list(self) -> list[str]:
        source_files = [
            path.relative_to(self.source_dir)
            for path in self.source_dir.rglob("*")
            if path.is_file() and any(path.match(mask) for mask in self.source_file_masks)
        ]
        source_files.sort(key=lambda path: (len(path.parts), path.as_posix()))
        return [path.as_posix() for path in source_files]

    def _get_source(self, source_name: str) -> str:
        return (self.source_dir / source_name).read_text(encoding="utf-8")
