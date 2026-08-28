import json
from copy import deepcopy


class MultiplayerRuntimeContractV1:
    """Fail-closed 1-4 player runtime contract.

    Certification scope is intentionally narrow: one player controls exactly one owned
    investigator; player-visible knowledge is projected from that investigator only;
    Keeper knowledge is never returned; party bindings must be unique.
    """

    MIN_PLAYERS = 1
    MAX_PLAYERS = 4

    @classmethod
    def validate_player_ids(cls, player_ids):
        if not isinstance(player_ids, list):
            return {"status": "BLOCKED", "code": "PLAYER_IDS_LIST_REQUIRED"}
        if not (cls.MIN_PLAYERS <= len(player_ids) <= cls.MAX_PLAYERS):
            return {"status": "BLOCKED", "code": "PLAYER_COUNT_OUT_OF_RANGE"}
        if any(not isinstance(pid, str) or not pid for pid in player_ids):
            return {"status": "BLOCKED", "code": "PLAYER_ID_INVALID"}
        if len(set(player_ids)) != len(player_ids):
            return {"status": "BLOCKED", "code": "DUPLICATE_PLAYER_ID"}
        return {"status": "PASS", "code": "PLAYER_IDS_VALID", "player_count": len(player_ids)}

    @classmethod
    def validate_party(cls, engine, player_ids):
        gate = cls.validate_player_ids(player_ids)
        if gate["status"] != "PASS":
            return gate
        bindings = {}
        character_ids = []
        for player_id in player_ids:
            row = engine.db.conn.execute(
                """SELECT p.character_id,c.owner_id
                   FROM party p JOIN characters c ON c.character_id=p.character_id
                   WHERE p.player_id=?""",
                (player_id,),
            ).fetchone()
            if not row:
                return {"status": "BLOCKED", "code": "PLAYER_CHARACTER_NOT_ATTACHED", "player_id": player_id}
            if row["owner_id"] != player_id:
                return {"status": "BLOCKED", "code": "PARTY_OWNER_MISMATCH", "player_id": player_id}
            bindings[player_id] = row["character_id"]
            character_ids.append(row["character_id"])
        if len(set(character_ids)) != len(character_ids):
            return {"status": "BLOCKED", "code": "DUPLICATE_CHARACTER_CONTROL"}
        return {
            "status": "PASS",
            "code": "MULTIPLAYER_PARTY_VALID",
            "player_count": len(player_ids),
            "control_map": {pid: [cid] for pid, cid in bindings.items()},
            "bindings": bindings,
        }

    @classmethod
    def player_projection(cls, engine, player_id):
        row = engine.db.conn.execute(
            """SELECT p.character_id,c.owner_id,c.state_json
               FROM party p JOIN characters c ON c.character_id=p.character_id
               WHERE p.player_id=?""",
            (player_id,),
        ).fetchone()
        if not row:
            return {"status": "BLOCKED", "code": "PLAYER_CHARACTER_NOT_ATTACHED"}
        if row["owner_id"] != player_id:
            return {"status": "BLOCKED", "code": "PARTY_OWNER_MISMATCH"}
        character_id = row["character_id"]
        player_knowledge = engine.knowledge.player_visible_ids(character_id)
        return {
            "status": "READY",
            "code": "PLAYER_MULTIPLAYER_PROJECTION_V1",
            "player_id": player_id,
            "character": {
                "character_id": character_id,
                "state": json.loads(row["state_json"]),
            },
            "knowledge": list(player_knowledge),
        }

    @classmethod
    def build_session_state(cls, engine, player_ids, session_id="MULTIPLAYER_CERT_V1"):
        party = cls.validate_party(engine, player_ids)
        if party["status"] != "PASS":
            return party
        character_states = []
        knowledge_state = {}
        for player_id in player_ids:
            projection = cls.player_projection(engine, player_id)
            if projection["status"] != "READY":
                return projection
            char = deepcopy(projection["character"]["state"])
            char["character_id"] = projection["character"]["character_id"]
            character_states.append(char)
            knowledge_state[player_id] = {"refs": list(projection["knowledge"])}
        _, revision = engine.db.state()
        return {
            "status": "READY",
            "code": "MULTIPLAYER_SESSION_STATE_V1",
            "session_state": {
                "session_id": session_id,
                "topology_id": "CERTIFICATION_NO_SCENARIO_EXECUTION",
                "scenario_state": {},
                "character_states": character_states,
                "knowledge_state": knowledge_state,
                "timeline": {},
                "revision": revision,
                "control_map": deepcopy(party["control_map"]),
                "scenario_public": {},
            },
        }
