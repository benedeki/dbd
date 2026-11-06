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
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dbd.core.simple_config import SimpleConfig

if TYPE_CHECKING:
    from dbd.abstract.abstract_secret_reader import AbstractSecretReader

class ExpandableConfig(SimpleConfig):
    """Configuration loaded from JSON with placeholder expansion support."""

    def __init__(self,
                 config_file: str,
                 cli_parameters: dict[str, str]):
        """Load a JSON configuration file.

        :param config_file: Path to the JSON configuration file.
        :param cli_parameters: Command-line values available to the ``CLI``
            placeholder.
        :return: None.
        :raises FileNotFoundError: If the configuration file does not exist.
        :raises json.JSONDecodeError: If the file is not valid JSON.
        :raises ValueError: If the JSON root is not an object.
        """
        config_file_path = Path(config_file)
        self._root = config_file_path.parent
        self._cli_parameters = cli_parameters
        loaded_data = self._load_file(config_file_path)
        if not isinstance(loaded_data, dict):
            raise ValueError(f"Configuration file must contain a JSON object: {config_file_path}")
        super().__init__(loaded_data)

    def expand(self, secret_reader: AbstractSecretReader | None = None, branch: str = ""):
        """Expand placeholders in the whole configuration or one branch.

        :param secret_reader: Reader used to resolve ``SECRET`` placeholders.
        :param branch: Root configuration key to expand; an empty string
            expands the complete configuration.
        :return: None.
        :raises ValueError: If a placeholder cannot be resolved.
        """
        data: dict[str, Any] = self.get_as_dict(branch) if branch else self._data
        self._expand_dict(data, secret_reader)

    def _expand_dict(self, data: dict, secret_reader: AbstractSecretReader | None) -> None:
        """Expand all values in a dictionary in place.

        :param data: Dictionary whose values should be expanded.
        :param secret_reader: Reader used to resolve ``SECRET`` placeholders.
        :return: None.
        """
        keys:list = list(data.keys())
        for key in keys:
            value = data[key]
            expanded_value = self._expand_value(value, secret_reader)
            if not isinstance(key, str):
                data.pop(key, None)
                data[str(key)] = expanded_value
            elif expanded_value != value:
                data[str(key)] = expanded_value

    def _expand_value(
        self,
        value: Any,
        secret_reader: AbstractSecretReader | None,
    ) -> Any:
        """Expand a value recursively.

        :param value: Value that may contain a placeholder, dictionary, or list.
        :param secret_reader: Reader used to resolve ``SECRET`` placeholders.
        :return: The expanded value.
        :raises ValueError: If a required reference value is unavailable or
            has an unknown type.
        """
        if isinstance(value, dict):
            self._expand_dict(value, secret_reader)
            return value
        if isinstance(value, list):
            return [self._expand_value(item, secret_reader) for item in value]
        if isinstance(value, str):
            match = REFERENCE_PATTERN.fullmatch(value)
            if match is None:
                return value
            reference_type: str = match.group("type")
            reference_value: str = match.group("value")
            match reference_type:
                case "FILE":
                    data = self._load_file(Path(reference_value))
                    return self._expand_value(data, secret_reader)
                case "SECRET":
                    if secret_reader is None:
                        raise ValueError(f"Secret reader is not provided for SECRET reference '{reference_value}'.")
                    secret = secret_reader.get_secret(reference_value)
                    return self._expand_value(secret, secret_reader)
                case "CLI":
                    cli_value = self._cli_parameters.get(reference_value)
                    if cli_value is None:
                        raise ValueError(f"CLI parameter '{reference_value}' has not been provided.")
                    return cli_value
                case "ENV":
                    env_value = os.getenv(reference_value)
                    if env_value is None:
                        raise ValueError(f"Environment variable '{reference_value}' is not set.")
                    return env_value
                case "CFG":
                    cfg_value = self.get(reference_value)
                    return self._expand_value(cfg_value, secret_reader)
                case _:
                    raise ValueError(f"Unknown reference type '{reference_type}'.")
        return value

    def _load_file(self, file_path: Path) -> Any:
        """Load JSON data from a path relative to the configuration file.

        :param file_path: Absolute path or path relative to the configuration
            file's directory.
        :return: The decoded JSON value.
        :raises FileNotFoundError: If the referenced file does not exist.
        :raises json.JSONDecodeError: If the referenced file is not valid JSON.
        """
        if not file_path.is_absolute():
            file_path = self._root / file_path
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)
        return data

REFERENCE_PATTERN = re.compile(r"^__(?P<type>[A-Z]+)\((?P<value>.+)\)$")
