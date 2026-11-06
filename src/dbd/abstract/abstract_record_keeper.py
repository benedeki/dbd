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


class AbstractRecordKeeper(Configurable, ABC):
    """Interface for tracking deployment sessions and source state."""

    @abstractmethod
    def start_session(self) -> None:
        """Start a deployment session.

        :return: None.
        """

    @abstractmethod
    def end_session(self, warnings: dict[str, str]) -> None:
        """End a deployment session.

        :param warnings: Mapping of source names to non-fatal warning messages.
        :return: None.
        """

    def fail_session(self, source_name: str, source_hash: str, error_message: str) -> None:
        """Record a failed deployment and terminate the session.

        :param source_name: Name of the source that failed.
        :param source_hash: Hash of the failed source.
        :param error_message: Description of the deployment failure.
        :return: None.
        :raises RuntimeError: When the default implementation is used.
        """
        raise RuntimeError(error_message)

    @abstractmethod
    def get_source_hash(self, source_name: str) -> str | None:
        """Get the previously recorded hash of a source.

        :param source_name: Name of the source to look up.
        :return: The recorded hash, or ``None`` when the source is unknown.
        """

    @abstractmethod
    def record_deploy(self, source_name: str, source_hash: str) -> None:
        """Record a successful or warning deployment.

        :param source_name: Name of the deployed source.
        :param source_hash: Hash of the deployed source.
        :return: None.
        """

    @abstractmethod
    def source_checked(self, source_name: str) -> None:
        """Record that an unchanged source was checked.

        :param source_name: Name of the source that was checked.
        :return: None.
        """
