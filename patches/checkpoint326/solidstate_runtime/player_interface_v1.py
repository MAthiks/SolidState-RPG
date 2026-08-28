from copy import deepcopy
from .playloop import ChoiceMenu


class PlayerInterfaceV1:
    """Strictly whitelisted player projection. Keeper state is never copied into the surface."""

    def __init__(self, engine):
        self.e = engine

    def _owned_character(self, player_id, character_id):
        row = self.e.db.conn.execute(
            "SELECT character_id FROM party WHERE player_id=?", (player_id,)
        ).fetchone()
        return bool(row and row["character_id"] == character_id)

    def _inventory(self, character_id):
        rows = self.e.db.conn.execute(
            """SELECT i.object_id,i.quantity,m.object_type
               FROM inventory i JOIN mechanical_registry m ON m.object_id=i.object_id
               WHERE i.owner_id=? AND i.quantity>0
               ORDER BY i.object_id""",
            (character_id,),
        ).fetchall()
        return [
            {"object_id": r["object_id"], "object_type": r["object_type"], "quantity": r["quantity"]}
            for r in rows
        ]

    def status_panel(self, player_id, character_id):
        if not self._owned_character(player_id, character_id):
            return {"status": "BLOCKED", "code": "CHARACTER_NOT_CONTROLLED_BY_PLAYER"}
        wound = self.e.wounds.state(character_id)
        hp = self.e.mechanics.get_value(character_id, "HP")
        san = self.e.mechanics.get_value(character_id, "SAN")
        pm = self.e.mechanics.get_value(character_id, "MP")
        if pm is None:
            pm = self.e.mechanics.get_value(character_id, "PM")
        luck = self.e.mechanics.get_value(character_id, "Luck")
        return {
            "status": "READY",
            "code": "PLAYER_STATUS_PANEL_V1",
            "character_id": character_id,
            "PV": hp,
            "SAN": san,
            "PM": pm,
            "Chance": luck,
            "conditions": {
                "blessure_majeure": bool(wound["major_wound"]) if wound else False,
                "mourant": bool(wound["dying"]) if wound else False,
            },
            "inventory": self._inventory(character_id),
        }

    def decision_prompt(self, player_id, character_id, mode="NORMAL_LIBRE", options=None):
        panel = self.status_panel(player_id, character_id)
        if panel["status"] != "READY":
            return panel
        if mode == "NORMAL_LIBRE":
            return {
                "status": "DECISION_READY",
                "code": "OPEN_PROMPT_ONLY",
                "prompt": "Que fais-tu ?",
                "menu": None,
                "status_panel": panel,
            }
        if mode != "FACILE_ASSISTE":
            return {"status": "BLOCKED", "code": "UNKNOWN_ASSISTANCE_MODE"}
        if not isinstance(options, list) or len(options) != 3:
            return {"status": "BLOCKED", "code": "EXACTLY_THREE_CHOICES_REQUIRED"}
        safe_options = []
        for opt in options:
            if not isinstance(opt, dict) or opt.get("visibility") != "PLAYER_SAFE":
                return {"status": "BLOCKED", "code": "CHOICE_NOT_PLAYER_SAFE"}
            for knowledge_id in opt.get("requires_knowledge", []):
                if not self.e.knowledge.can_expose(character_id, knowledge_id):
                    return {"status": "BLOCKED", "code": "CHOICE_KNOWLEDGE_NOT_VISIBLE"}
            safe_options.append({"id": opt.get("id"), "label": opt.get("label")})
        menu = ChoiceMenu.build(safe_options)
        if menu["status"] != "RESOLVED":
            return menu
        return {
            "status": "DECISION_READY",
            "code": "ASSISTED_THREE_PLUS_FREE",
            "prompt": "Que fais-tu ?",
            "menu": menu,
            "status_panel": panel,
        }


class LaunchChainV1:
    """Fail-closed scenario -> validation -> players -> characters -> session readiness chain."""

    def __init__(self, engine, scenario_selection):
        self.e = engine
        self.scenario_selection = scenario_selection

    def _party_binding(self, player_id):
        row = self.e.db.conn.execute(
            """SELECT p.character_id,c.owner_id
               FROM party p JOIN characters c ON c.character_id=p.character_id
               WHERE p.player_id=?""",
            (player_id,),
        ).fetchone()
        if not row or row["owner_id"] != player_id:
            return None
        return row["character_id"]

    def prepare_session(self, scenario_key, player_ids):
        trace = []
        selected = self.scenario_selection.select(scenario_key)
        trace.append({"gate": "SCENARIO", "result": selected["status"], "code": selected["code"]})
        if selected["status"] != "SELECTED":
            return {"status": "BLOCKED", "code": selected["code"], "trace": trace}
        if not isinstance(player_ids, list) or not (1 <= len(player_ids) <= 4) or len(set(player_ids)) != len(player_ids):
            trace.append({"gate": "PLAYERS", "result": "BLOCKED", "code": "PLAYER_COUNT_OR_ID_INVALID"})
            return {"status": "BLOCKED", "code": "PLAYER_COUNT_OR_ID_INVALID", "trace": trace}
        trace.append({"gate": "PLAYERS", "result": "PASS", "count": len(player_ids)})
        bindings = {}
        for player_id in player_ids:
            character_id = self._party_binding(player_id)
            if not character_id:
                trace.append({"gate": "CHARACTER", "result": "BLOCKED", "player_id": player_id, "code": "PLAYER_CHARACTER_NOT_READY"})
                return {"status": "BLOCKED", "code": "PLAYER_CHARACTER_NOT_READY", "trace": trace}
            bindings[player_id] = character_id
        trace.append({"gate": "CHARACTERS", "result": "PASS", "count": len(bindings)})
        session_record = {
            "interface_version": "PLAYER_INTERFACE_V1",
            "scenario_key": scenario_key,
            "scenario_title": selected["selection"]["title"],
            "certification_status": selected["selection"]["certification_status"],
            "players": list(player_ids),
            "control_map": bindings,
            "phase": "SESSION_READY",
        }
        def mutate(state):
            state["interface_session"] = deepcopy(session_record)
        tx = self.e.transact(mutate, ["interface_session"])
        if tx["status"] != "COMMIT":
            trace.append({"gate": "SESSION", "result": "ROLLBACK", "code": "SESSION_TRANSACTION_FAILED"})
            return {"status": "ROLLBACK", "code": "SESSION_TRANSACTION_FAILED", "trace": trace}
        trace.append({"gate": "SESSION", "result": "PASS", "commit": tx["new_commit"]})
        return {
            "status": "SESSION_READY",
            "code": "LAUNCH_CHAIN_V1_READY",
            "commit": tx["new_commit"],
            "session": session_record,
            "trace": trace,
        }
