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
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dbd.abstract.abstract_secret_reader import AbstractSecretReader

class Config:
    _data: dict[str, Any]

    def __init__(self, data: dict[str, Any]):
        self._data = data


    @classmethod
    def from_file(cls, filename: str, root: str | None= None) -> "Config":
        root_path = Path(root) if root is not None else None
        data = cls._from_file(filename, root_path)
        return cls(data)

    @classmethod
    def _from_file(cls, filename: str, root: Path | None= None) -> dict[str, Any]:
        file_path = Path(filename)
        if not file_path.is_absolute() and root is not None:
            file_path = root / file_path
        containing_dir = file_path.parent
        data = cls._load_file(file_path)
        data = cls._expand_config(data, containing_dir)
        return data

    @classmethod
    def _expand_config(
        cls,
        data: dict[str, Any],
        root: Path,
        secret_reader: AbstractSecretReader | None = None
    ) -> dict[str, Any]:
        expanded = dict(data)
        for key, value in expanded.items():
            if not isinstance(value, str):
                continue

            match = REFERENCE_PATTERN.fullmatch(value)
            if match is None:
                continue

            reference_type: str = match.group("type")
            reference_value: str = match.group("value")
            match reference_type:
                case "FILE":
                    expanded[key] = cls._from_file(reference_value, root)
                case "SECRET" if secret_reader:
                    secret = secret_reader.get_secret(reference_value)
                    if secret is not None:
                        expanded[key] = secret
                case _:
                    continue

        return expanded

    @classmethod
    def _load_file(cls, file_path: Path) -> dict[str, Any]:
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(f"Configuration file must contain a JSON object: {file_path}")

        return data

    def expand(self, secret_reader: AbstractSecretReader):
        self._data = self._expand_config(self._data, Path.cwd(), secret_reader)


REFERENCE_PATTERN = re.compile(r"^__(?P<type>[A-Z]+)\((?P<value>.+)\)$")
