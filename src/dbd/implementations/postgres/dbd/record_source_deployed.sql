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

CREATE OR REPLACE FUNCTION dbd.record_source_deployed(
    IN  i_session_id                    UUID,
    IN  i_source_name                   TEXT,
    IN  i_source_hash                   TEXT,
    OUT first_deployment_session_id    UUID
)RETURNS UUID AS $$
-------------------------------------------------------------------------------
--
-- Function: dbd.record_source_deployed(3)
--      Records the deployment of a source in the dbd.sources table, updating the source_hash and session IDs for last
--      deployment and last check. If the source does not exist, it inserts a new record with the provided information.
--
-- Parameters:
--      i_session_id                    - The ID of the session
--      i_source_name                   - The name of the source
--      i_source_hash                   - The hash of the source
--
-- Returns:
--      first_deployment_session_id    - The ID of the first deployment session of the source
--
-------------------------------------------------------------------------------
DECLARE
   _record_timestamp    TIMESTAMP WITH TIME ZONE := clock_timestamp();
   _group_id            TEXT;
BEGIN

    SELECT S.group_id
    FROM dbd.sessions S
    WHERE S.session_id = i_session_id
    INTO _group_id;

    IF NOT found  THEN
        RAISE EXCEPTION 'Session ID % not found in dbd.sessions', i_session_id;
    END IF;

    UPDATE dbd.sources
    SET
        source_hash = i_source_hash,
        session_id_of_last_deployment = i_session_id,
        session_id_of_last_check = i_session_id,
        last_deployed_at = _record_timestamp,
        last_check_at = _record_timestamp
    WHERE source_name = i_source_name
        AND group_id = _group_id
    RETURNING session_id_of_first_deployment
    INTO first_deployment_session_id;

    IF NOT found THEN
        INSERT INTO dbd.sources (
            group_id,
            source_name,
            source_hash,
            session_id_of_first_deployment,
            session_id_of_last_deployment,
            session_id_of_last_check,
            last_deployed_at,
            last_check_at
        ) VALUES (
            _group_id,
            i_source_name,
            i_source_hash,
            i_session_id,
            i_session_id,
            i_session_id,
            _record_timestamp,
            _record_timestamp
        );

       first_deployment_session_id := i_session_id;
    END IF;

    RETURN;
END;
$$ LANGUAGE plpgsql VOLATILE SECURITY DEFINER;

ALTER FUNCTION dbd.record_source_deployed(UUID, TEXT, TEXT) OWNER TO dbd_owner;

GRANT EXECUTE ON FUNCTION dbd.record_source_deployed(UUID, TEXT, TEXT) TO dbd_user;
