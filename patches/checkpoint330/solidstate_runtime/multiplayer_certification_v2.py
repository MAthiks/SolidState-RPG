import json
from copy import deepcopy


class MultiplayerRuntimeContractV2:
    """Strict 1-4 player ownership, control and knowledge partition contract.

    V2 closes split-brain cases between canonical state and SQL projections and requires
    the active party set to match the certified player set exactly.
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
    def validate_party(cls, engine, player_ids, require_interface=False):
        gate = cls.validate_player_ids(player_ids)
        if gate["status"] != "PASS":
            return gate

        sql_rows = engine.db.conn.execute(
            "SELECT player_id,character_id FROM party ORDER BY player_id"
        ).fetchall()
        sql_party = {r["player_id"]: r["character_id"] for r in sql_rows}
        if set(sql_party) != set(player_ids):
            return {"status": "BLOCKED", "code": "PARTY_PLAYER_SET_MISMATCH", "party_players": sorted(sql_party)}
        if any(not cid for cid in sql_party.values()):
            return {"status": "BLOCKED", "code": "PLAYER_CHARACTER_NOT_ATTACHED"}
        if len(set(sql_party.values())) != len(player_ids):
            return {"status": "BLOCKED", "code": "DUPLICATE_CHARACTER_CONTROL"}

        state, revision = engine.db.state()
        canonical_party = state.get("party")
        if not isinstance(canonical_party, dict) or canonical_party != sql_party:
            return {"status": "BLOCKED", "code": "CANONICAL_SQL_PARTY_MISMATCH"}

        bindings = {}
        for player_id in player_ids:
            cid = sql_party[player_id]
            row = engine.db.conn.execute(
                "SELECT owner_id,state_json FROM characters WHERE character_id=?", (cid,)
            ).fetchone()
            if not row:
                return {"status": "BLOCKED", "code": "CHARACTER_NOT_FOUND", "player_id": player_id}
            if row["owner_id"] != player_id:
                return {"status": "BLOCKED", "code": "PARTY_OWNER_MISMATCH", "player_id": player_id}
            try:
                json.loads(row["state_json"])
            except Exception:
                return {"status": "BLOCKED", "code": "CHARACTER_STATE_INVALID", "player_id": player_id}
            bindings[player_id] = cid

        interface = state.get("interface_session")
        if require_interface or interface is not None:
            if not isinstance(interface, dict) or interface.get("phase") != "SESSION_READY":
                return {"status": "BLOCKED", "code": "INTERFACE_SESSION_NOT_READY"}
            if interface.get("players") != list(player_ids):
                return {"status": "BLOCKED", "code": "INTERFACE_PLAYER_SET_MISMATCH"}
            if interface.get("control_map") != bindings:
                return {"status": "BLOCKED", "code": "INTERFACE_CONTROL_MAP_MISMATCH"}

        return {
            "status": "PASS",
            "code": "MULTIPLAYER_PARTY_V2_VALID",
            "player_count": len(player_ids),
            "revision": revision,
            "bindings": deepcopy(bindings),
            "control_map": {pid: [cid] for pid, cid in bindings.items()},
        }

    @classmethod
    def player_projection(cls, engine, player_id):
        if not isinstance(player_id, str) or not player_id:
            return {"status": "BLOCKED", "code": "PLAYER_ID_INVALID"}
        row = engine.db.conn.execute(
            """SELECT p.character_id,c.owner_id,c.state_json
               FROM party p JOIN characters c ON c.character_id=p.character_id
               WHERE p.player_id=?""", (player_id,)
        ).fetchone()
        if not row:
            return {"status": "BLOCKED", "code": "PLAYER_CHARACTER_NOT_ATTACHED"}
        state, _ = engine.db.state()
        cid = row["character_id"]
        if row["owner_id"] != player_id or state.get("party", {}).get(player_id) != cid:
            return {"status": "BLOCKED", "code": "PLAYER_CONTROL_OWNERSHIP_MISMATCH"}
        try:
            char_state = json.loads(row["state_json"])
        except Exception:
            return {"status": "BLOCKED", "code": "CHARACTER_STATE_INVALID"}

        player_knowledge = engine.knowledge.player_visible_ids(cid)
        if len(player_knowledge) != len(set(player_knowledge)):
            return {"status": "BLOCKED", "code": "DUPLICATE_PLAYER_KNOWLEDGE"}
        keeper_rows = engine.db.conn.execute(
            "SELECT knowledge_id FROM knowledge_partitions WHERE character_id=? AND visibility='KEEPER'",
            (cid,),
        ).fetchall()
        keeper_ids = {r["knowledge_id"] for r in keeper_rows}
        if keeper_ids.intersection(player_knowledge):
            return {"status": "BLOCKED", "code": "KEEPER_KNOWLEDGE_EXPOSED"}

        return {
            "status": "READY",
            "code": "PLAYER_MULTIPLAYER_PROJECTION_V2",
            "player_id": player_id,
            "character": {"character_id": cid, "state": char_state},
            "knowledge": list(player_knowledge),
        }

    @classmethod
    def build_session_state(cls, engine, player_ids, session_id="MULTIPLAYER_CERT_V2"):
        party = cls.validate_party(engine, player_ids)
        if party["status"] != "PASS":
            return party
        character_states = []
        knowledge_state = {}
        for pid in player_ids:
            projection = cls.player_projection(engine, pid)
            if projection["status"] != "READY":
                return projection
            c = deepcopy(projection["character"]["state"])
            c["character_id"] = projection["character"]["character_id"]
            character_states.append(c)
            knowledge_state[pid] = {"refs": list(projection["knowledge"])}
        return {
            "status": "READY",
            "code": "MULTIPLAYER_SESSION_STATE_V2",
            "session_state": {
                "session_id": session_id,
                "character_states": character_states,
                "knowledge_state": knowledge_state,
                "revision": party["revision"],
                "control_map": deepcopy(party["control_map"]),
                "scenario_public": {},
            },
        }
