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


CREATE TABLE IF NOT EXISTS dbd.sessions (
    id_session_id               UUID NOT NULL PRIMARY KEY
        COMMENT 'Unique identifier for the session.',
    group_id                    TEXT,
        COMMENT 'Allows to identify the session by group it belongs to (e.g. "users db deployment").',
    session_start               TIMESTAMP WITH TIME ZONE NOT NULL
        COMMENT 'Timestamp when the session started.',
    session_end                 TIMESTAMP WITH TIME ZONE
        COMMENT 'Timestamp when the session ended.',
    session_ended_as_success    BOOLEAN
        COMMENT 'Indicates whether the session ended successfully.',
    session_log                 JSONB
        COMMENT 'Log of the session in JSONB format.',
);

ALTER TABLE SET OWNER dbd.sessions TO ROLE dbd_owner;
COMMENT ON TABLE dbd.sessions IS 'Table to track sessions of deployments.';

CREATE INDEX IF NOT EXISTS idx_sessions_group_id
    ON dbd.sessions (group_id, session_start DESC);
