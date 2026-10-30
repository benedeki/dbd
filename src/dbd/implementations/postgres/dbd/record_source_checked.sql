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

CREATE OR REPLACE FUNCTION dbd.record_source_checked(
    IN  i_session_id                    UUID,
    IN  i_source_name                   TEXT,
    OUT first_deployment_session_id    UUID
)RETURNS UUID AS $$
-------------------------------------------------------------------------------
--
-- Function: dbd.record_source_checked(2)
--      Records that a source has been checked.
--
-- Parameters:
--      i_session_id                    - The ID of the session
--      i_source_name                   - The name of the source
--
-- Returns:
--      first_deployment_session_id     - The ID of the first deployment session of the source, or NULL if the source
--                                        has never been deployed
--
-------------------------------------------------------------------------------
DECLARE
   _group_id            TEXT;
BEGIN

    SELECT S.group_id
    FROM dbd.sessions S
    WHERE S.session_id = i_session_id
    INTO _group_id;

    IF NOT found  THEN
        RAISE EXCEPTION 'Session key % not found in dbd.sessions', i_session_id;
    END IF;

    UPDATE dbd.sources
    SET
        session_id_of_last_check = i_session_id,
        last_check_at = clock_timestamp()
    WHERE source_name = i_source_name
        AND group_id = _group_id
    RETURNING session_id_of_first_deployment
    INTO first_deployment_session_id;

    RETURN;
END;
$$ LANGUAGE plpgsql VOLATILE SECURITY DEFINER;

ALTER FUNCTION dbd.record_source_checked(UUID, TEXT) OWNER TO dbd_owner;

GRANT EXECUTE ON FUNCTION dbd.record_source_checked(UUID, TEXT) TO dbd_user;
