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

from __future__ import annotations

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
    def from_file(
        cls,
        filename: str,
        root: str | None = None,
        secret_reader: AbstractSecretReader | None = None,
    ) -> Config:
        root_path = Path(root) if root is not None else None
        data = cls._from_file(filename, root_path, secret_reader)
        return cls(data)

    @classmethod
    def _from_file(
        cls,
        filename: str,
        root: Path | None = None,
        secret_reader: AbstractSecretReader | None = None,
    ) -> dict[str, Any]:
        file_path = Path(filename)
        if not file_path.is_absolute() and root is not None:
            file_path = root / file_path
        containing_dir = file_path.parent
        data = cls._load_file(file_path)
        return cls._expand_config(data, containing_dir, secret_reader)

    @classmethod
    def _expand_value(
        cls,
        value: Any,
        root: Path,
        secret_reader: AbstractSecretReader | None = None,
    ) -> Any:
        if isinstance(value, dict):
            return {key: cls._expand_value(val, root, secret_reader) for key, val in value.items()}
        if isinstance(value, list):
            return [cls._expand_value(item, root, secret_reader) for item in value]
        if isinstance(value, str):
            match = REFERENCE_PATTERN.fullmatch(value)
            if match is None:
                return value
            reference_type: str = match.group("type")
            reference_value: str = match.group("value")
            match reference_type:
                case "FILE":
                    return cls._from_file(reference_value, root)
                case "SECRET" if secret_reader:
                    secret = secret_reader.get_secret(reference_value)
                    return secret if secret is not None else value
                case _:
                    return value
        return value

    @classmethod
    def _expand_config(
        cls,
        data: dict[str, Any],
        root: Path,
        secret_reader: AbstractSecretReader | None = None,
    ) -> dict[str, Any]:
        return {key: cls._expand_value(val, root, secret_reader) for key, val in data.items()}

    @classmethod
    def _load_file(cls, file_path: Path) -> dict[str, Any]:
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(f"Configuration file must contain a JSON object: {file_path}")

        return data

    def expand(self, secret_reader: AbstractSecretReader):
        self._data = self._expand_config(self._data, Path.cwd(), secret_reader)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str) -> Any:
        return self._data[key]

    def get_as_str(self, key: str, default: str | None = None) -> str:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        if isinstance(value, list):
            result = "\n".join(str(x) for x in value)
            return result
        return str(value)

    def get_as_int(self, key: str, default: int | None = None) -> int:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        return int(value)

    def get_as_bool(self, key: str, default: bool | None = None) -> bool:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        if isinstance(value, bool):
            return value
        lowered = str(value).strip().lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off"):
            return False
        raise ValueError(f"Cannot interpret '{value}' as boolean")

    def get_as_float(self, key: str, default: float | None = None) -> float:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        return float(value)

    def get_as_list(self, key: str, default: list[Any] | None = None) -> list[Any]:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        if not isinstance(value, list):
            value = [value]
        return value

    def get_as_dict(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        if not isinstance(value, dict):
            raise ValueError(f"Configuration key '{key}' is not a dictionary.")
        return value

    def get_as_config(self, key: str, default: dict[str, Any] | None = None) -> Config:
        return Config(self.get_as_dict(key, default))

REFERENCE_PATTERN = re.compile(r"^__(?P<type>[A-Z]+)\((?P<value>.+)\)$")
