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

from dbd.core.config import Config
from dbd.implementations.file.source_provider import SourceProvider


def test_get_sources_list_returns_matching_files_with_direct_files_first(tmp_path):
    (tmp_path / "b.sql").write_text("b", encoding="utf-8")
    (tmp_path / "a.sql").write_text("a", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("ignored", encoding="utf-8")
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    (nested_dir / "z.sql").write_text("z", encoding="utf-8")
    deeper_dir = nested_dir / "deeper"
    deeper_dir.mkdir()
    (deeper_dir / "a.sql").write_text("a", encoding="utf-8")

    source_provider = SourceProvider(Config({"path": str(tmp_path), "file_masks": ["*.sql"]}))

    assert source_provider.get_sources_list() == [
        "a.sql",
        "b.sql",
        "nested/z.sql",
        "nested/deeper/a.sql",
    ]


def test_get_source_reads_file_relative_to_source_dir(tmp_path):
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    (nested_dir / "source.sql").write_text("CREATE TABLE example;", encoding="utf-8")

    source_provider = SourceProvider(Config({"path": str(tmp_path), "file_masks": ["*.sql"]}))

    assert source_provider.get_source("nested/source.sql") == "CREATE TABLE example;"
