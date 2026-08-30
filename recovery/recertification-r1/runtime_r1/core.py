from __future__ import annotations

import copy
import hashlib
import hmac
import json
import secrets
import sqlite3

SCHEMA = "SOLIDSTATE_RECOVERY_RUNTIME_R1_B_V1"
AUTHORITY_ID = "RECOVERY_RECERTIFICATION_R1_B"
CHECKPOINT_FLOOR = 333


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(obj):
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


class RecoveryRuntimeR1:
    def __init__(self, db_path, secret=b"recovery-r1-test-secret"):
        self.db_path = str(db_path)
        self.secret = bytes(secret)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._schema()

    def _schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS characters(
              character_id TEXT PRIMARY KEY,
              owner_id TEXT NOT NULL,
              state_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS party(
              player_id TEXT PRIMARY KEY,
              character_id TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS knowledge(
              character_id TEXT NOT NULL,
              knowledge_id TEXT NOT NULL,
              visibility TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              PRIMARY KEY(character_id,knowledge_id)
            );
            """
        )
        self.conn.commit()

    def close(self):
        self.conn.close()

    def _get_state(self):
        row = self.conn.execute("SELECT value FROM meta WHERE key='state'").fetchone()
        return json.loads(row["value"]) if row else None

    def _put_state(self, state):
        self.conn.execute(
            "INSERT INTO meta(key,value) VALUES('state',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (canon(state),),
        )

    def _sync_tables(self, state):
        self.conn.execute("DELETE FROM characters")
        self.conn.execute("DELETE FROM party")
        self.conn.execute("DELETE FROM knowledge")
        for cid, character in state["characters"].items():
            self.conn.execute(
                "INSERT INTO characters VALUES(?,?,?)",
                (cid, character["owner_id"], canon(character)),
            )
        for pid, cid in state["party"].items():
            self.conn.execute("INSERT INTO party VALUES(?,?)", (pid, cid))
        for cid, entries in state["knowledge"].items():
            for kid, entry in entries.items():
                self.conn.execute(
                    "INSERT INTO knowledge VALUES(?,?,?,?)",
                    (cid, kid, entry["visibility"], canon(entry["payload"])),
                )

    def _commit_state(self, state):
        with self.conn:
            self._put_state(state)
            self._sync_tables(state)

    @staticmethod
    def _players_ok(players):
        return (
            isinstance(players, list)
            and 1 <= len(players) <= 4
            and all(isinstance(player, dict) for player in players)
        )

    def new_session(self, players, session_id="R1-B-SESSION"):
        if not self._players_ok(players):
            return {"status": "BLOCKED", "code": "PLAYER_COUNT_OR_SHAPE_INVALID"}
        player_ids = [f"P{i + 1}" for i in range(len(players))]
        party = {}
        characters = {}
        knowledge = {}
        for i, (pid, player) in enumerate(zip(player_ids, players), 1):
            cid = f"C{i}"
            party[pid] = cid
            characters[cid] = {
                "character_id": cid,
                "owner_id": pid,
                "name": player.get("name", cid),
                "stats": copy.deepcopy(player.get("stats", {})),
                "inventory": copy.deepcopy(player.get("inventory", [])),
            }
            knowledge[cid] = {}
        state = {
            "schema": SCHEMA,
            "authority_floor": CHECKPOINT_FLOOR,
            "session_id": session_id,
            "commit_sequence": 0,
            "interface_session": {
                "phase": "SESSION_READY",
                "players": player_ids,
                "control_map": party.copy(),
            },
            "party": party,
            "characters": characters,
            "initial_characters": copy.deepcopy(characters),
            "knowledge": knowledge,
            "journal": [],
        }
        self._commit_state(state)
        return {
            "status": "SESSION_READY",
            "players": player_ids,
            "control_map": party.copy(),
        }

    def state(self):
        return copy.deepcopy(self._get_state())

    def state_digest(self):
        return sha(self._get_state())

    def add_knowledge(self, character_id, knowledge_id, visibility, payload):
        state = self._get_state()
        before = sha(state)
        if (
            state is None
            or character_id not in state["characters"]
            or visibility not in ("PLAYER", "KEEPER")
            or not knowledge_id
        ):
            return {"status": "FAIL_CLOSED", "code": "KNOWLEDGE_INVALID", "digest": before}
        state["knowledge"][character_id][knowledge_id] = {
            "visibility": visibility,
            "payload": copy.deepcopy(payload),
        }
        state["commit_sequence"] += 1
        self._commit_state(state)
        return {"status": "COMMIT", "commit_sequence": state["commit_sequence"]}

    def player_view(self, player_id):
        state = self._get_state()
        cid = state["party"].get(player_id)
        if not cid:
            return {"status": "BLOCKED", "code": "PLAYER_NOT_IN_SESSION"}
        entries = []
        for kid, entry in state["knowledge"].get(cid, {}).items():
            if entry["visibility"] == "PLAYER":
                entries.append(
                    {"knowledge_id": kid, "payload": copy.deepcopy(entry["payload"])}
                )
        return {
            "status": "READY",
            "player_id": player_id,
            "character": copy.deepcopy(state["characters"][cid]),
            "knowledge": entries,
        }

    @staticmethod
    def _event_hash(previous_hash, event):
        return hashlib.sha256(
            (previous_hash + "\n" + canon(event)).encode("utf-8")
        ).hexdigest()

    def roll_d100(self):
        return {
            "expression": "1d100",
            "result": secrets.randbelow(100) + 1,
            "provenance": "python.secrets.randbelow / OS CSPRNG",
        }

    def append_player_action(
        self, player_id, character_id, action_id, roll, delta=0, event_id=None
    ):
        state = self._get_state()
        before = sha(state)
        control_map = state["interface_session"]["control_map"]
        if control_map.get(player_id) != character_id:
            return {
                "status": "FAIL_CLOSED",
                "code": "ACTOR_CONTROL_MISMATCH",
                "before": before,
                "after": before,
            }
        if not isinstance(roll, int) or isinstance(roll, bool) or not 1 <= roll <= 100:
            return {
                "status": "FAIL_CLOSED",
                "code": "ROLL_INVALID",
                "before": before,
                "after": before,
            }
        if not isinstance(delta, int) or isinstance(delta, bool):
            return {
                "status": "FAIL_CLOSED",
                "code": "DELTA_INVALID",
                "before": before,
                "after": before,
            }
        eid = event_id or f"{state['session_id']}:{state['commit_sequence'] + 1}:{player_id}"
        if any(row["event"]["event_id"] == eid for row in state["journal"]):
            return {
                "status": "FAIL_CLOSED",
                "code": "DUPLICATE_EVENT_ID",
                "before": before,
                "after": before,
            }
        event = {
            "event_id": eid,
            "action_id": str(action_id),
            "payload": {
                "player_id": player_id,
                "character_id": character_id,
                "roll": roll,
                "delta": delta,
            },
        }
        previous_hash = (
            state["journal"][-1]["event_hash"] if state["journal"] else "GENESIS"
        )
        row = {
            "event": event,
            "previous_hash": previous_hash,
            "event_hash": self._event_hash(previous_hash, event),
        }
        hp = state["characters"][character_id].setdefault("stats", {}).get("HP")
        if delta and not isinstance(hp, (int, float)):
            return {
                "status": "FAIL_CLOSED",
                "code": "MECHANICAL_HP_MISSING",
                "before": before,
                "after": before,
            }
        state["journal"].append(row)
        if delta:
            state["characters"][character_id]["stats"]["HP"] = hp + delta
        state["commit_sequence"] += 1
        self._commit_state(state)
        return {
            "status": "COMMIT",
            "event_id": eid,
            "commit_sequence": state["commit_sequence"],
            "event_hash": row["event_hash"],
        }

    @classmethod
    def verify_journal(cls, state, expected_actor_trace=None):
        previous_hash = "GENESIS"
        seen = set()
        trace = []
        replay_characters = copy.deepcopy(state["initial_characters"])
        control_map = state["interface_session"]["control_map"]
        for index, row in enumerate(state["journal"]):
            event = row.get("event", {})
            event_id = event.get("event_id")
            payload = event.get("payload", {})
            if not event_id or event_id in seen:
                return {
                    "status": "REPLAY_DIVERGENCE",
                    "reason": "DUPLICATE_OR_MISSING_EVENT_ID",
                    "index": index,
                }
            seen.add(event_id)
            if (
                row.get("previous_hash") != previous_hash
                or row.get("event_hash") != cls._event_hash(previous_hash, event)
            ):
                return {
                    "status": "REPLAY_DIVERGENCE",
                    "reason": "HASH_CHAIN_INVALID",
                    "index": index,
                }
            player_id = payload.get("player_id")
            character_id = payload.get("character_id")
            roll = payload.get("roll")
            delta = payload.get("delta", 0)
            if control_map.get(player_id) != character_id:
                return {
                    "status": "REPLAY_DIVERGENCE",
                    "reason": "ACTOR_CONTROL_MISMATCH",
                    "index": index,
                }
            if not isinstance(roll, int) or isinstance(roll, bool) or not 1 <= roll <= 100:
                return {
                    "status": "REPLAY_DIVERGENCE",
                    "reason": "ROLL_INVALID",
                    "index": index,
                }
            if delta:
                hp = replay_characters[character_id].setdefault("stats", {}).get("HP")
                if not isinstance(hp, (int, float)):
                    return {
                        "status": "REPLAY_DIVERGENCE",
                        "reason": "MECHANICAL_HP_MISSING",
                        "index": index,
                    }
                replay_characters[character_id]["stats"]["HP"] = hp + delta
            trace.append(
                {
                    "event_id": event_id,
                    "action_id": event.get("action_id"),
                    "player_id": player_id,
                    "character_id": character_id,
                    "roll": roll,
                    "event_hash": row["event_hash"],
                }
            )
            previous_hash = row["event_hash"]
        if replay_characters != state["characters"]:
            return {
                "status": "REPLAY_DIVERGENCE",
                "reason": "CANONICAL_STATE_MISMATCH",
            }
        if expected_actor_trace is not None and trace != expected_actor_trace:
            return {
                "status": "REPLAY_DIVERGENCE",
                "reason": "ACTOR_TRACE_MISMATCH",
                "actual": trace,
                "expected": expected_actor_trace,
            }
        return {"status": "REPLAY_MATCH", "events": len(trace), "actor_trace": trace}

    def continuity_fingerprint(self):
        state = self._get_state()
        verification = self.verify_journal(state)
        return {
            "commit_sequence": state["commit_sequence"],
            "canonical_digest": sha(state),
            "journal_hashes": [row["event_hash"] for row in state["journal"]],
            "rolls": [row["event"]["payload"]["roll"] for row in state["journal"]],
            "actions": [row["event"]["action_id"] for row in state["journal"]],
            "actor_trace": verification.get("actor_trace", []),
        }

    def _bundle_payload(self):
        return {
            "schema": "SOLIDSTATE_RECOVERY_SAVE_R1_B_V1",
            "checkpoint_floor": CHECKPOINT_FLOOR,
            "authority_id": AUTHORITY_ID,
            "state": self._get_state(),
        }

    def save_bundle(self):
        payload = self._bundle_payload()
        raw = canon(payload).encode("utf-8")
        return {
            "payload": payload,
            "auth": {
                "algorithm": "HMAC-SHA256",
                "payload_sha256": hashlib.sha256(raw).hexdigest(),
                "hmac_sha256": hmac.new(
                    self.secret, raw, hashlib.sha256
                ).hexdigest(),
            },
        }

    def restore_bundle(self, bundle):
        before = self.state_digest()
        try:
            if set(bundle) != {"payload", "auth"}:
                raise ValueError("BUNDLE_SHAPE_INVALID")
            payload = bundle["payload"]
            auth = bundle["auth"]
            raw = canon(payload).encode("utf-8")
            if (
                payload.get("schema") != "SOLIDSTATE_RECOVERY_SAVE_R1_B_V1"
                or payload.get("checkpoint_floor") != CHECKPOINT_FLOOR
                or payload.get("authority_id") != AUTHORITY_ID
            ):
                raise ValueError("AUTHORITY_FLOOR_INVALID")
            if hashlib.sha256(raw).hexdigest() != auth.get("payload_sha256"):
                raise ValueError("PAYLOAD_HASH_MISMATCH")
            expected = hmac.new(self.secret, raw, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, str(auth.get("hmac_sha256", ""))):
                raise ValueError("SAVE_AUTHENTICATION_FAILED")
            state = copy.deepcopy(payload["state"])
            if state.get("authority_floor") != CHECKPOINT_FLOOR:
                raise ValueError("STATE_AUTHORITY_FLOOR_INVALID")
            if self.verify_journal(state).get("status") != "REPLAY_MATCH":
                raise ValueError("STRICT_REPLAY_INVALID")
            self._commit_state(state)
            return {
                "status": "RESTORED_STRICT",
                "commit_sequence": state["commit_sequence"],
            }
        except Exception as error:
            return {
                "status": "FAIL_CLOSED",
                "code": str(error),
                "before": before,
                "after": self.state_digest(),
            }
