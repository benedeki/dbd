/*
 * Copyright 2026 David Benedeki, All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


CREATE TABLE IF NOT EXISTS dbd.sources (
    group_id                        TEXT NOT NULL,
    source_name                     TEXT NOT NULL,
    source_hash                     TEXT NOT NULL,
    session_id_of_first_deployment UUID NOT NULL,
    session_id_of_last_deployment  UUID,
    session_id_of_last_check       UUID,
    last_deployed_at                TIMESTAMP WITH TIME ZONE,
    last_check_at                   TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (group_id, source_name)
);

ALTER TABLE dbd.sources OWNER TO dbd_owner;

COMMENT ON TABLE dbd.sources IS 'Table to track deployment of sources.';
COMMENT ON COLUMN dbd.sources.group_id IS 'Group identifier for the source.';
COMMENT ON COLUMN dbd.sources.source_name IS 'Name of the source.';
COMMENT ON COLUMN dbd.sources.source_hash IS 'Hash of the source content.';
COMMENT ON COLUMN dbd.sources.session_id_of_first_deployment IS 'Identifier of the session that first deployed this source.';
COMMENT ON COLUMN dbd.sources.session_id_of_last_deployment IS 'Identifier of the session that last deployed this source.';
COMMENT ON COLUMN dbd.sources.session_id_of_last_check IS 'Identifier of the session that last checked this source, no necessary deploy.';
COMMENT ON COLUMN dbd.sources.last_deployed_at IS 'Timestamp of the last deployment of this source.';
COMMENT ON COLUMN dbd.sources.last_check_at IS 'Timestamp of the last time this source was checked, no necessary deploy.';

CREATE INDEX IF NOT EXISTS idx_sources_group_id_source_name
    ON dbd.sources (group_id, source_name);

