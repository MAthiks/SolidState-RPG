from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BATCH5_DIR = ROOT / 'development' / 'r1-coc7-registry-batch5'
if str(BATCH5_DIR) not in sys.path:
    sys.path.insert(0, str(BATCH5_DIR))

import registry_batch5_dev as parent  # noqa: E402

EQUIPMENT_DOC = json.loads((HERE / 'equipment_batch1.json').read_text(encoding='utf-8'))
WEAPON_DOC = json.loads((HERE / 'weapons_batch1.json').read_text(encoding='utf-8'))
REGISTRY_ID = 'COC7_RECOVERY_EQUIPMENT_WEAPONS_R1_BATCH1_DEV_V1'
PARENT_REGISTRY_ID = parent.REGISTRY_ID
FROZEN_ANCESTOR_REGISTRY_ID = parent.FROZEN_ANCESTOR_REGISTRY_ID
SOURCE_ID = EQUIPMENT_DOC['source']['source_id']
SOURCE_SHA256 = EQUIPMENT_DOC['source']['sha256']
EQUIPMENT = EQUIPMENT_DOC['equipment']
WEAPONS = WEAPON_DOC['weapons']
SKILL_EXTENSIONS = WEAPON_DOC['skill_extensions']


def resolve_skill(skill_id: str, *, dex: int | None = None, edu: int | None = None, era: str | None = None) -> dict:
    key = str(skill_id).upper()
    record = SKILL_EXTENSIONS.get(key)
    if record is None:
        return parent.resolve_skill(key, dex=dex, edu=edu, era=era)
    out = copy.deepcopy(record)
    out['skill_id'] = key
    return {
        'status': 'RESOLVED',
        'registry_id': REGISTRY_ID,
        'parent_registry_id': PARENT_REGISTRY_ID,
        'source_id': SOURCE_ID,
        'source_sha256': SOURCE_SHA256,
        'record': out,
    }


def resolve_equipment(equipment_id: str) -> dict:
    key = str(equipment_id).upper()
    record = EQUIPMENT.get(key)
    if record is None:
        return {'status': 'BLOCKED', 'code': 'EQUIPMENT_RECORD_UNMATERIALIZED', 'equipment_id': equipment_id}
    return {
        'status': 'RESOLVED_REFERENCE',
        'registry_id': REGISTRY_ID,
        'parent_registry_id': PARENT_REGISTRY_ID,
        'source_id': SOURCE_ID,
        'source_sha256': SOURCE_SHA256,
        'record': copy.deepcopy(record),
        'auto_possession': False,
    }


def resolve_weapon(weapon_id: str) -> dict:
    key = str(weapon_id).upper()
    record = WEAPONS.get(key)
    if record is None:
        return {'status': 'BLOCKED', 'code': 'WEAPON_RECORD_UNMATERIALIZED', 'weapon_id': weapon_id}
    skill = resolve_skill(record['skill_id'], dex=50, edu=50, era='1920S')
    if skill.get('status') != 'RESOLVED':
        return {
            'status': 'BLOCKED',
            'code': 'WEAPON_SKILL_RECORD_UNRESOLVED',
            'weapon_id': key,
            'skill_id': record['skill_id'],
        }
    return {
        'status': 'RESOLVED_MECHANICS',
        'registry_id': REGISTRY_ID,
        'parent_registry_id': PARENT_REGISTRY_ID,
        'source_id': SOURCE_ID,
        'source_sha256': SOURCE_SHA256,
        'record': copy.deepcopy(record),
        'auto_possession': False,
    }


def validate_all_references() -> dict:
    unresolved = []
    for weapon_id in WEAPONS:
        result = resolve_weapon(weapon_id)
        if result.get('status') != 'RESOLVED_MECHANICS':
            unresolved.append({'weapon_id': weapon_id, 'result': result})
    return {
        'status': 'PASS' if not unresolved else 'FAIL',
        'weapon_count': len(WEAPONS),
        'unresolved': unresolved,
    }


def frozen_c4_weapon_compatibility() -> dict:
    checks = {
        'REVOLVER_38_OR_9MM': {
            'damage': '1D10', 'base_range_yards': 15, 'uses_per_round': '1 (3)', 'capacity': '6', 'malfunction': 100
        },
        'LEE_ENFIELD_303': {
            'damage': '2D6+4', 'base_range_yards': 110, 'uses_per_round': '1', 'capacity': '10', 'malfunction': 100
        },
        'THOMPSON_SMG': {
            'damage': '1D10+2', 'base_range_yards': 20, 'uses_per_round': '1 OR FULL_AUTO', 'capacity': '20/30/50', 'malfunction': 96
        },
    }
    failures = []
    for wid, expected in checks.items():
        record = WEAPONS[wid]
        range_value = record['base_range']
        if range_value.endswith(' yards') and range_value.split()[0].isdigit():
            range_yards = int(range_value.split()[0])
        else:
            range_yards = None
        actual = {
            'damage': record['damage'],
            'base_range_yards': range_yards,
            'uses_per_round': record['uses_per_round'],
            'capacity': record['capacity'],
            'malfunction': record['malfunction'],
        }
        if actual != expected:
            failures.append({'weapon_id': wid, 'actual': actual, 'expected': expected})
    return {'status': 'PASS' if not failures else 'FAIL', 'checked': len(checks), 'failures': failures}


def registry_summary() -> dict:
    return {
        'registry_id': REGISTRY_ID,
        'parent_registry_id': PARENT_REGISTRY_ID,
        'frozen_ancestor_registry_id': FROZEN_ANCESTOR_REGISTRY_ID,
        'source_sha256': SOURCE_SHA256,
        'equipment_count': len(EQUIPMENT),
        'weapon_count': len(WEAPONS),
        'skill_extensions': len(SKILL_EXTENSIONS),
        'auto_possession': False,
        'authority_promoted': False,
        'frozen_parent_modified': False,
    }
