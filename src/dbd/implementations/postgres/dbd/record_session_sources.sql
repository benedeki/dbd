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

CREATE OR REPLACE FUNCTION dbd.record_session_sources(
    IN  i_session_id                    UUID,
    IN  i_deployed_sources              TEXT[],
    IN  i_deployed_hashes               TEXT[],
    IN  i_checked_sources               TEXT[],
    OUT sources_deployed                INTEGER,
    OUT sources_redeployed              INTEGER,
    OUT sources_checked                 INTEGER,
    OUT checked_sources_not_found       INTEGER
) RETURNS record AS $$
-------------------------------------------------------------------------------
--
-- Function: dbd.record_session_sources(4)
--      Records the sources deployed and checked for a given session. It counts the number of sources deployed for the
--      first time, redeployed, checked, and checked but not found.
--
-- Parameters:
--      i_session_id                    - The ID of the session
--      i_deployed_sources              - The array of deployed source names
--      i_deployed_hashes               - The array of deployed source hashes
--      i_checked_sources               - The array of checked source names
--
-- Returns:
--      sources_deployed                - The number of sources deployed for the first time
--      sources_redeployed              - The number of sources redeployed
--      sources_checked                 - The number of sources checked
--      checked_sources_not_found       - The number of checked sources not found (reported as checked but record does not exist)
--
-------------------------------------------------------------------------------
DECLARE
   _rec         RECORD;
   _uuid        UUID;
   _source_name TEXT;
BEGIN
    sources_deployed := 0;
    sources_redeployed := 0;
    sources_checked := 0;
    checked_sources_not_found := 0;

    FOR _rec IN
        SELECT unnest(i_deployed_sources) AS source_name, unnest(i_deployed_hashes) AS source_hash
    LOOP
        SELECT FDKS.first_deployment_key_session
        FROM dbd.record_source_deployed(
            i_session_id,
            _rec.source_name,
            _rec.source_hash
        ) FDKS
        INTO _uuid;

        IF _uuid = i_session_id THEN
            sources_deployed := sources_deployed + 1;
        ELSE
            sources_redeployed := sources_redeployed + 1;
        END IF;
    END LOOP;

    FOR _source_name IN
        SELECT unnest(i_checked_sources) AS source_name
    LOOP
        SELECT FDKS.first_deployment_key_session
        FROM dbd.record_source_checked(
            i_session_id,
            _source_name
        ) FDKS
        INTO _uuid;

        IF _uuid IS NULL THEN
            checked_sources_not_found := checked_sources_not_found + 1;
        ELSE
            sources_checked := sources_checked + 1;
        END IF;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql VOLATILE SECURITY DEFINER;

ALTER FUNCTION dbd.record_session_sources(UUID, TEXT[], TEXT[], TEXT[]) OWNER TO dbd_owner;
