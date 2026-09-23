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
from typing import Any

from dbd.core.configurable import Configurable


class AbstractSecretReader(Configurable, ABC):
    """Abstract interface for reading secrets from external secret stores."""

    @abstractmethod
    def get_secret(self, secret_name: str) -> str | dict[str, Any] | list[Any] | None:
        """Return a secret of the given name."""

    def get_secret_str(self, secret_name: str) -> str:
        """Return a secret of the given name as a string."""
        result = self.get_secret(secret_name)
        if not isinstance(result, str):
            raise ValueError(f"Secret '{secret_name}' does not exist or is not a string.")
        return result

    def get_secret_dict(self, secret_name: str) -> dict[str, Any]:
        """Return a secret of the given name as a dictionary."""
        result = self.get_secret(secret_name)
        if not isinstance(result, dict):
            raise ValueError(f"Secret '{secret_name}' does not exist or is not a dictionary.")
        return result

    def get_secret_list(self, secret_name: str) -> list:
        """Return a list of secrets of the given names as strings."""
        result = self.get_secret(secret_name)
        if not isinstance(result, list):
            raise ValueError(f"Secret '{secret_name}' does not exist or is not a list.")
        return result
