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

from dbd.core.config import Config
from dbd.core.configurable import Configurable


class AbstractRecordKeeper(Configurable, ABC):
    @abstractmethod
    def start_session(self, full_config: Config):
        """Start a session with the record keeper."""

    @abstractmethod
    def end_session(self, warnings: dict[str, str]):
        """End the session with the record keeper."""

    def fail_session(self, source_name: str, source_hash: str, error_message: str):
        """Fail the session with the record keeper."""
        raise RuntimeError(error_message)

    @abstractmethod
    def check_source_for_deploy(self, source_name: str, source_hash: str) -> bool:
        """Check the status of a given source."""

    @abstractmethod
    def record(self, source_name: str, source_hash: str):
        """Record the deployment event."""
