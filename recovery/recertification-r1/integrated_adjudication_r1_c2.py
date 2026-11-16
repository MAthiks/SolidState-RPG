from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from runtime_r1.core import RecoveryRuntimeR1
from rules_r1.core_rules import (
    PACKAGE_ID as RULES_PACKAGE_ID,
    classify_damage,
    derived_stats,
    firearm_difficulty,
    meets_difficulty,
    opposed,
    sanity_transition,
)
from source_adapter_r1 import verify_source

INTEGRATION_ID = "SOLIDSTATE_RECOVERY_RUNTIME_R1_C2_V1"
RULES_ZIP_SHA256 = "c18ad9763b44eb0d2864bc61ab01aa709eda604f4318af8498e6759df8f4b8c2"
RULES_MANIFEST_SHA256 = "db5e1a6daff660fdbb5df61b71ce569dc8e6c87841c17f485f76745c83a92a22"

MECHANIC_SOURCE = {
    "SKILL_CHECK": "COC7_KEEPER",
    "OPPOSED": "COC7_KEEPER",
    "DAMAGE_AFTER_HIT": "COC7_KEEPER",
    "SANITY_LOSS": "COC7_KEEPER",
    "FIREARM_RANGE": "COC7_KEEPER",
    "DERIVED_STATS": "COC7_INVESTIGATOR",
}


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SourceBackedRuntimeR1C2(RecoveryRuntimeR1):
    def __init__(self, db_path, rules_zip, source_paths, secret=b"recovery-r1-test-secret"):
        super().__init__(db_path, secret)
        self.rules_zip = str(rules_zip)
        self.source_paths = dict(source_paths)

    def _rules_identity(self):
        path = Path(self.rules_zip)
        if not path.is_file():
            return {"status": "BLOCKED", "code": "RULES_PACKAGE_MISSING"}
        actual = _sha256_file(path)
        if actual != RULES_ZIP_SHA256:
            return {
                "status": "BLOCKED",
                "code": "RULES_PACKAGE_HASH_MISMATCH",
                "expected_sha256": RULES_ZIP_SHA256,
                "actual_sha256": actual,
            }
        try:
            with zipfile.ZipFile(path) as archive:
                candidates = [name for name in archive.namelist() if name.endswith("/PACKAGE_MANIFEST.json")]
                if len(candidates) != 1:
                    raise ValueError("RULES_MANIFEST_COUNT_INVALID")
                raw = archive.read(candidates[0])
                manifest = json.loads(raw.decode("utf-8"))
        except Exception as error:
            return {"status": "BLOCKED", "code": "RULES_PACKAGE_INVALID", "detail": str(error)}
        if (
            manifest.get("package_id") != RULES_PACKAGE_ID
            or manifest.get("claims_historical_4_7_identity") is not False
        ):
            return {"status": "BLOCKED", "code": "RULES_MANIFEST_IDENTITY_INVALID"}
        manifest_sha = hashlib.sha256(raw).hexdigest()
        if manifest_sha != RULES_MANIFEST_SHA256:
            return {
                "status": "BLOCKED",
                "code": "RULES_MANIFEST_HASH_MISMATCH",
                "actual_sha256": manifest_sha,
            }
        return {
            "status": "VERIFIED",
            "package_id": RULES_PACKAGE_ID,
            "zip_sha256": actual,
            "manifest_sha256": manifest_sha,
        }

    def _preflight(self, mechanic, scenario_sources=()):
        rules = self._rules_identity()
        if rules["status"] != "VERIFIED":
            return {"status": "BLOCKED", "code": rules["code"], "rules": rules}
        rule_source = MECHANIC_SOURCE.get(mechanic)
        if rule_source is None:
            return {"status": "BLOCKED", "code": "MECHANIC_UNMATERIALIZED", "mechanic": mechanic}
        required = [rule_source] + list(scenario_sources)
        verified = []
        for source_id in required:
            result = verify_source(source_id, self.source_paths.get(source_id, ""))
            if result["status"] != "VERIFIED":
                return {
                    "status": "BLOCKED",
                    "code": "SOURCE_PREFLIGHT_FAILED",
                    "failed_source": source_id,
                    "source_result": result,
                    "rules": rules,
                }
            verified.append(
                {
                    "source_id": source_id,
                    "sha256": result["sha256"],
                    "role": result["role"],
                }
            )
        return {"status": "VERIFIED", "rules": rules, "sources": verified}

    def _actor_ok(self, player_id, character_id):
        state = self.state()
        return state is not None and state["party"].get(player_id) == character_id

    def adjudicate_skill(
        self,
        *,
        player_id,
        character_id,
        skill_value,
        difficulty="REGULAR",
        scenario_sources=(),
        recorded_roll=None,
        replay=False,
        event_id=None,
    ):
        before = self.state_digest()
        if not self._actor_ok(player_id, character_id):
            return {
                "status": "FAIL_CLOSED",
                "code": "ACTOR_CONTROL_MISMATCH",
                "before": before,
                "after": before,
            }
        preflight = self._preflight("SKILL_CHECK", scenario_sources)
        if preflight["status"] != "VERIFIED":
            return {
                "status": "FAIL_CLOSED",
                "code": preflight["code"],
                "preflight": preflight,
                "before": before,
                "after": before,
            }
        if recorded_roll is None:
            dice = self.roll_d100()
        elif replay:
            dice = {
                "expression": "1d100",
                "result": recorded_roll,
                "provenance": "recorded roll / strict replay input",
            }
        else:
            return {
                "status": "FAIL_CLOSED",
                "code": "RECORDED_ROLL_REQUIRES_REPLAY_MODE",
                "before": before,
                "after": before,
            }
        outcome = meets_difficulty(skill_value, dice["result"], difficulty)
        commit = self.append_player_action(
            player_id,
            character_id,
            f"SKILL:{difficulty}",
            dice["result"],
            0,
            event_id=event_id,
        )
        if commit["status"] != "COMMIT":
            return {
                "status": "FAIL_CLOSED",
                "code": commit.get("code", "COMMIT_FAILED"),
                "before": before,
                "after": self.state_digest(),
            }
        return {
            "status": "COMMIT",
            "integration_id": INTEGRATION_ID,
            "actor": {"player_id": player_id, "character_id": character_id},
            "rules": preflight["rules"],
            "sources": preflight["sources"],
            "dice": dice,
            "outcome": outcome,
            "state_delta": {},
            "commit_sequence": commit["commit_sequence"],
            "event_hash": commit["event_hash"],
        }

    def adjudicate_damage_after_hit(
        self,
        *,
        player_id,
        character_id,
        skill_value,
        attack_roll,
        damage,
        scenario_sources=(),
        event_id=None,
        damage_provenance="recorded damage result",
    ):
        before_state = self.state()
        before_digest = self.state_digest()
        if not self._actor_ok(player_id, character_id):
            return {
                "status": "FAIL_CLOSED",
                "code": "ACTOR_CONTROL_MISMATCH",
                "before": before_digest,
                "after": before_digest,
            }
        preflight = self._preflight("DAMAGE_AFTER_HIT", scenario_sources)
        if preflight["status"] != "VERIFIED":
            return {
                "status": "FAIL_CLOSED",
                "code": preflight["code"],
                "preflight": preflight,
                "before": before_digest,
                "after": before_digest,
            }
        hit = meets_difficulty(skill_value, attack_roll, "REGULAR")
        if not hit["success"]:
            commit = self.append_player_action(
                player_id,
                character_id,
                "ATTACK:MISS",
                attack_roll,
                0,
                event_id=event_id,
            )
            return {
                "status": commit["status"],
                "integration_id": INTEGRATION_ID,
                "rules": preflight["rules"],
                "sources": preflight["sources"],
                "attack": hit,
                "damage_applied": 0,
                "state_delta": {},
            }
        hp = before_state["characters"][character_id].get("stats", {}).get("HP")
        if not isinstance(hp, (int, float)):
            return {
                "status": "FAIL_CLOSED",
                "code": "MECHANICAL_HP_MISSING",
                "before": before_digest,
                "after": before_digest,
            }
        max_hp = before_state["initial_characters"][character_id].get("stats", {}).get("HP")
        classification = classify_damage(int(max_hp), int(hp), int(damage))
        delta = int(classification["current_hp"] - hp)
        commit = self.append_player_action(
            player_id,
            character_id,
            "ATTACK:HIT_DAMAGE",
            attack_roll,
            delta,
            event_id=event_id,
        )
        if commit["status"] != "COMMIT":
            return {
                "status": "FAIL_CLOSED",
                "code": commit.get("code", "COMMIT_FAILED"),
                "before": before_digest,
                "after": self.state_digest(),
            }
        return {
            "status": "COMMIT",
            "integration_id": INTEGRATION_ID,
            "rules": preflight["rules"],
            "sources": preflight["sources"],
            "attack": {"roll": attack_roll, **hit},
            "damage": {
                "amount": damage,
                "provenance": damage_provenance,
                "classification": classification,
            },
            "state_delta": {
                f"characters.{character_id}.stats.HP": {"op": "add", "value": delta}
            },
            "commit_sequence": commit["commit_sequence"],
            "event_hash": commit["event_hash"],
        }

    def adjudicate_sanity_loss(
        self,
        *,
        player_id,
        character_id,
        loss,
        sanity_start_of_day,
        daily_loss_before=0,
        scenario_sources=(),
        commit=False,
    ):
        before = self.state_digest()
        if not self._actor_ok(player_id, character_id):
            return {
                "status": "FAIL_CLOSED",
                "code": "ACTOR_CONTROL_MISMATCH",
                "before": before,
                "after": before,
            }
        preflight = self._preflight("SANITY_LOSS", scenario_sources)
        if preflight["status"] != "VERIFIED":
            return {
                "status": "FAIL_CLOSED",
                "code": preflight["code"],
                "preflight": preflight,
                "before": before,
                "after": before,
            }
        state = self.state()
        current_san = state["characters"][character_id].get("stats", {}).get("SAN")
        if not isinstance(current_san, int):
            return {
                "status": "FAIL_CLOSED",
                "code": "MECHANICAL_SAN_MISSING",
                "before": before,
                "after": before,
            }
        outcome = sanity_transition(
            current_san=current_san,
            sanity_start_of_day=sanity_start_of_day,
            loss=loss,
            daily_loss_before=daily_loss_before,
        )
        if commit:
            return {
                "status": "FAIL_CLOSED",
                "code": "SAN_MUTATION_NOT_MATERIALIZED_R1_C2",
                "outcome": outcome,
                "before": before,
                "after": before,
            }
        return {
            "status": "RESOLVED_READ_ONLY",
            "integration_id": INTEGRATION_ID,
            "rules": preflight["rules"],
            "sources": preflight["sources"],
            "outcome": outcome,
            "state_delta": {},
        }

    def derive_investigator_stats(self, *, characteristics, age, scenario_sources=()):
        preflight = self._preflight("DERIVED_STATS", scenario_sources)
        if preflight["status"] != "VERIFIED":
            return {
                "status": "FAIL_CLOSED",
                "code": preflight["code"],
                "preflight": preflight,
            }
        result = derived_stats(age=age, **characteristics)
        return {
            "status": "RESOLVED_READ_ONLY",
            "integration_id": INTEGRATION_ID,
            "rules": preflight["rules"],
            "sources": preflight["sources"],
            "result": result,
        }

    def resolve_opposed(self, *, value_a, roll_a, value_b, roll_b, scenario_sources=()):
        preflight = self._preflight("OPPOSED", scenario_sources)
        if preflight["status"] != "VERIFIED":
            return {
                "status": "FAIL_CLOSED",
                "code": preflight["code"],
                "preflight": preflight,
            }
        return {
            "status": "RESOLVED_READ_ONLY",
            "integration_id": INTEGRATION_ID,
            "rules": preflight["rules"],
            "sources": preflight["sources"],
            "result": opposed(value_a, roll_a, value_b, roll_b),
        }

    def resolve_firearm_range(self, *, distance, base_range, scenario_sources=()):
        preflight = self._preflight("FIREARM_RANGE", scenario_sources)
        if preflight["status"] != "VERIFIED":
            return {
                "status": "FAIL_CLOSED",
                "code": preflight["code"],
                "preflight": preflight,
            }
        return {
            "status": "RESOLVED_READ_ONLY",
            "integration_id": INTEGRATION_ID,
            "rules": preflight["rules"],
            "sources": preflight["sources"],
            "difficulty": firearm_difficulty(distance, base_range),
        }
