from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH1_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch1'
REGISTRY_DIR = ROOT / 'development' / 'r1-coc7-registry-batch5'
for path in (BATCH1_DIR, REGISTRY_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import investigator_creation_dev as batch1  # noqa: E402
import registry_batch5_dev as registry  # noqa: E402

MODULE_ID = 'COC7_INVESTIGATOR_CREATION_R1_BATCH2_DEV_V1'
PARENT_MODULE_ID = batch1.MODULE_ID
PARENT_HARDENED_PROOF = 2414
INVESTIGATOR_SOURCE_ID = 'COC7_INVESTIGATOR'
INVESTIGATOR_SHA256 = batch1.INVESTIGATOR_SHA256
REGISTRY_ID = registry.REGISTRY_ID
REQUIRED_BACKSTORY = (
    'PERSONAL_DESCRIPTION',
    'IDEOLOGY_BELIEFS',
    'SIGNIFICANT_PEOPLE',
    'MEANINGFUL_LOCATIONS',
    'TREASURED_POSSESSIONS',
    'TRAITS',
)
OPTIONAL_BACKSTORY = (
    'INJURIES_SCARS',
    'PHOBIAS_MANIAS',
    'ARCANE_TOMES_SPELLS_ARTIFACTS',
    'ENCOUNTERS_WITH_STRANGE_ENTITIES',
)
SUPPORTED_SLOT_KEYS = {
    'skill', 'specialization', 'specialization_choice', 'required_specialization',
    'count', 'choice_one_of', 'choice_one_of_families', 'choice_n_of',
    'interpersonal_choice', 'allowed', 'personal_or_era_specialty',
    'academic_or_personal_specialty', 'field_of_study', 'personal_specialty',
    'skill_family', 'notes', 'note', 'era_scope', 'era_variant', 'restriction',
    'specialist_reading_topic_allowed', 'trade_specialty_allowed', 'keeper_authorized_option',
}
PLACEHOLDER_SPECIALIZATIONS = {
    'ANY', 'ANY_OTHER', 'TRADE_ANY', 'INSTRUMENT', 'ALPINE_OR_APPROPRIATE',
    'INVESTIGATOR_LANGUAGE',
}
GENERIC_SPECIALTY_KEYS = {
    'personal_or_era_specialty', 'academic_or_personal_specialty', 'field_of_study', 'personal_specialty',
}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _norm(value: str) -> str:
    return str(value).strip().upper().replace(' ', '_').replace('-', '_')


def _all_occupation_records() -> dict:
    modules = [
        registry,
        registry.batch4,
        registry.batch4.batch3,
        registry.batch4.batch3.batch2,
        registry.batch4.batch3.batch2.batch1,
    ]
    out = {}
    for module in modules:
        out.update(module.OCCUPATIONS)
    return out


def _materialized_science_specializations() -> set[str]:
    found = set()

    def inspect(item):
        if not isinstance(item, dict):
            return
        family = _norm(item.get('skill_family', '')) if item.get('skill_family') else None
        skill = _norm(item.get('skill', '')) if item.get('skill') else None
        if family == 'SCIENCE' or skill == 'SCIENCE':
            required = item.get('required_specialization')
            if isinstance(required, str) and _norm(required) not in PLACEHOLDER_SPECIALIZATIONS:
                found.add(_norm(required))
            spec = item.get('specialization')
            if isinstance(spec, str) and _norm(spec) not in PLACEHOLDER_SPECIALIZATIONS:
                found.add(_norm(spec))
            for value in item.get('specialization_choice', []) if isinstance(item.get('specialization_choice'), list) else []:
                if isinstance(value, str) and value.strip():
                    found.add(_norm(value))
        for alt in item.get('choice_one_of', []) if isinstance(item.get('choice_one_of'), list) else []:
            inspect(alt)
        plan = item.get('choice_n_of')
        if isinstance(plan, dict):
            for alt in plan.get('choices', []) if isinstance(plan.get('choices'), list) else []:
                inspect(alt)

    for record in _all_occupation_records().values():
        for slot in record.get('skill_slots', []):
            inspect(slot)
    return found


def occupation_slot_schema_audit() -> dict:
    unsupported = []
    bad_count = []
    for occupation_id, record in sorted(_all_occupation_records().items()):
        slots = record.get('skill_slots')
        if not isinstance(slots, list):
            unsupported.append({'occupation_id': occupation_id, 'code': 'SKILL_SLOTS_NOT_LIST'})
            continue
        count = 0
        for index, slot in enumerate(slots):
            if not isinstance(slot, dict):
                unsupported.append({'occupation_id': occupation_id, 'slot': index, 'code': 'SLOT_NOT_DICT'})
                continue
            unknown = sorted(set(slot) - SUPPORTED_SLOT_KEYS)
            if unknown:
                unsupported.append({'occupation_id': occupation_id, 'slot': index, 'unknown_keys': unknown})
            n = slot.get('count', 1)
            if not _valid_int(n, 1, 8):
                unsupported.append({'occupation_id': occupation_id, 'slot': index, 'code': 'SLOT_COUNT_INVALID'})
            else:
                count += n
            if 'specialization_choice' in slot:
                choices = slot['specialization_choice']
                if not isinstance(choices, list) or not choices or not all(isinstance(x, str) and x.strip() for x in choices):
                    unsupported.append({'occupation_id': occupation_id, 'slot': index, 'code': 'SPECIALIZATION_CHOICE_SCHEMA_INVALID'})
            if 'choice_one_of_families' in slot:
                families = slot['choice_one_of_families']
                if not isinstance(families, list) or not families or not all(isinstance(x, str) and x.strip() for x in families):
                    unsupported.append({'occupation_id': occupation_id, 'slot': index, 'code': 'FAMILY_CHOICE_SCHEMA_INVALID'})
            if 'choice_n_of' in slot:
                plan = slot['choice_n_of']
                if not isinstance(plan, dict) or not _valid_int(plan.get('n'), 1) or not isinstance(plan.get('choices'), list) or not plan['choices']:
                    unsupported.append({'occupation_id': occupation_id, 'slot': index, 'code': 'CHOICE_N_SCHEMA_INVALID'})
                elif int(plan['n']) != int(n):
                    unsupported.append({'occupation_id': occupation_id, 'slot': index, 'code': 'CHOICE_N_COUNT_MISMATCH'})
        if count != 8:
            bad_count.append({'occupation_id': occupation_id, 'count': count})
    return {
        'status': 'PASS' if not unsupported and not bad_count else 'BLOCKED',
        'occupation_count': len(_all_occupation_records()),
        'unsupported': unsupported,
        'bad_slot_counts': bad_count,
    }


def _expanded_slots(record: dict) -> list[dict]:
    expanded = []
    for source_index, slot in enumerate(record['skill_slots']):
        count = int(slot.get('count', 1))
        for copy_index in range(count):
            expanded.append({'source_slot_index': source_index, 'copy_index': copy_index, 'slot': copy.deepcopy(slot)})
    return expanded


def _resolve_skill_record(skill_id: str, specialization: str | None, *, characteristics: dict, era: str) -> dict:
    requested = _norm(skill_id)
    specialization_norm = _norm(specialization) if specialization else None
    if requested == 'SCIENCE' and specialization_norm and specialization_norm not in _materialized_science_specializations():
        return {
            'status': 'BLOCKED',
            'code': 'SCIENCE_SPECIALIZATION_UNMATERIALIZED',
            'skill_id': requested,
            'specialization': specialization_norm,
        }
    candidates = [requested]
    if specialization_norm:
        candidates.insert(0, f'{requested}_{specialization_norm}')
    for candidate in candidates:
        r = registry.resolve_skill(candidate, dex=characteristics.get('DEX'), edu=characteristics.get('EDU'), era=era)
        if r.get('status') == 'RESOLVED':
            record = copy.deepcopy(r['record'])
            base = record.get('base')
            if not _valid_int(base, 0, 100):
                return {'status': 'BLOCKED', 'code': 'SKILL_BASE_UNRESOLVED', 'skill_id': candidate}
            canonical_key = candidate
            if candidate == requested and specialization_norm:
                canonical_key = f'{requested}:{specialization_norm}'
            return {
                'status': 'RESOLVED',
                'skill_id': requested,
                'specialization': specialization_norm,
                'canonical_key': canonical_key,
                'registry_skill_id': candidate,
                'base': base,
                'record': record,
            }
    return {'status': 'BLOCKED', 'code': 'SKILL_OR_SPECIALIZATION_UNRESOLVED', 'skill_id': requested, 'specialization': specialization_norm}


def _specialization_matches(expected, sid: str, spec: str | None, base_skill: str) -> bool:
    if expected is None:
        return sid == base_skill
    token = _norm(expected)
    if token in PLACEHOLDER_SPECIALIZATIONS:
        return (sid == base_skill and bool(spec)) or sid.startswith(base_skill + '_')
    return spec == token or sid == f'{base_skill}_{token}'


def _alternative_match(alt: dict, selection: dict) -> bool:
    sid = _norm(selection.get('skill_id', ''))
    spec = _norm(selection.get('specialization')) if selection.get('specialization') else None
    if 'skill' in alt:
        expected = _norm(alt['skill'])
        if 'specialization_choice' in alt:
            allowed = {_norm(x) for x in alt['specialization_choice']}
            return (sid == expected and spec in allowed) or any(sid == f'{expected}_{x}' for x in allowed)
        expected_spec = alt.get('specialization')
        if expected_spec is not None:
            return _specialization_matches(expected_spec, sid, spec, expected)
        return sid == expected
    if 'skill_family' in alt:
        family = _norm(alt['skill_family'])
        if not (sid == family or sid.startswith(family + '_')):
            return False
        required = alt.get('required_specialization')
        if required:
            return spec == _norm(required) or sid == f'{family}_{_norm(required)}'
        return sid != family or bool(spec)
    return False


def _generic_specialty_matches(selection: dict, *, keeper_authorized_mythos: bool) -> dict:
    sid = _norm(selection.get('skill_id', ''))
    if not sid:
        return {'status': 'BLOCKED', 'code': 'OCCUPATION_SKILL_ID_REQUIRED'}
    if sid == 'CTHULHU_MYTHOS' and not keeper_authorized_mythos:
        return {'status': 'BLOCKED', 'code': 'CTHULHU_MYTHOS_STARTING_SKILL_REQUIRES_KEEPER_AUTHORIZATION'}
    return {'status': 'MATCHED'}


def _slot_matches(slot: dict, selection: dict, *, keeper_authorized_mythos: bool) -> dict:
    sid = _norm(selection.get('skill_id', ''))
    spec = _norm(selection.get('specialization')) if selection.get('specialization') else None
    if not sid:
        return {'status': 'BLOCKED', 'code': 'OCCUPATION_SKILL_ID_REQUIRED'}

    if 'skill' in slot:
        expected = _norm(slot['skill'])
        if 'specialization_choice' in slot:
            allowed = {_norm(x) for x in slot['specialization_choice']}
            if not ((sid == expected and spec in allowed) or any(sid == f'{expected}_{x}' for x in allowed)):
                return {'status': 'BLOCKED', 'code': 'OCCUPATION_SPECIALIZATION_CHOICE_INVALID', 'allowed': sorted(allowed)}
        else:
            expected_spec = slot.get('specialization')
            if expected_spec is not None:
                if not _specialization_matches(expected_spec, sid, spec, expected):
                    code = 'OCCUPATION_SPECIALIZATION_REQUIRED' if _norm(expected_spec) in PLACEHOLDER_SPECIALIZATIONS else 'OCCUPATION_FIXED_SPECIALIZATION_MISMATCH'
                    return {'status': 'BLOCKED', 'code': code}
            elif sid != expected:
                return {'status': 'BLOCKED', 'code': 'OCCUPATION_SKILL_SLOT_MISMATCH'}
        return {'status': 'MATCHED'}

    if 'skill_family' in slot:
        family = _norm(slot['skill_family'])
        if not (sid == family or sid.startswith(family + '_')):
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_SKILL_FAMILY_MISMATCH'}
        required = slot.get('required_specialization')
        if required:
            fixed = _norm(required)
            if not (spec == fixed or sid == f'{family}_{fixed}'):
                return {'status': 'BLOCKED', 'code': 'OCCUPATION_FIXED_SPECIALIZATION_MISMATCH'}
        elif sid == family and not spec:
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_SPECIALIZATION_REQUIRED'}
        return {'status': 'MATCHED'}

    if 'choice_one_of' in slot:
        choices = slot['choice_one_of']
        if not isinstance(choices, list) or not choices or not all(isinstance(x, dict) for x in choices):
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_CHOICE_SCHEMA_INVALID'}
        if not any(_alternative_match(alt, selection) for alt in choices):
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_CHOICE_NOT_ALLOWED'}
        return {'status': 'MATCHED'}

    if 'choice_one_of_families' in slot:
        families = tuple(_norm(x) for x in slot['choice_one_of_families'])
        matched_family = next((family for family in families if sid == family or sid.startswith(family + '_')), None)
        if matched_family is None:
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_FAMILY_CHOICE_NOT_ALLOWED', 'allowed': list(families)}
        if sid == matched_family and not spec:
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_SPECIALIZATION_REQUIRED'}
        return {'status': 'MATCHED'}

    if 'choice_n_of' in slot:
        plan = slot['choice_n_of']
        choices = plan.get('choices') if isinstance(plan, dict) else None
        if not isinstance(choices, list) or not choices or not all(isinstance(x, dict) for x in choices):
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_CHOICE_N_SCHEMA_INVALID'}
        if not any(_alternative_match(alt, selection) for alt in choices):
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_CHOICE_NOT_ALLOWED'}
        return {'status': 'MATCHED'}

    if slot.get('interpersonal_choice'):
        allowed = tuple(_norm(x) for x in (slot.get('allowed') or registry.INTERPERSONAL))
        if sid not in allowed:
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_INTERPERSONAL_CHOICE_INVALID', 'allowed': list(allowed)}
        return {'status': 'MATCHED'}

    if any(slot.get(key) for key in GENERIC_SPECIALTY_KEYS):
        generic = _generic_specialty_matches(selection, keeper_authorized_mythos=keeper_authorized_mythos)
        if generic['status'] != 'MATCHED':
            return generic
        option = slot.get('keeper_authorized_option')
        if isinstance(option, dict) and _norm(option.get('skill', '')) == sid:
            if not keeper_authorized_mythos:
                return {'status': 'BLOCKED', 'code': 'KEEPER_AUTHORIZED_OCCUPATION_OPTION_REQUIRED'}
            advised = option.get('advised_starting_max')
            points = selection.get('points', 0)
            if _valid_int(advised, 0) and _valid_int(points, 0) and points > advised:
                return {'status': 'BLOCKED', 'code': 'KEEPER_AUTHORIZED_OPTION_ADVISED_MAX_EXCEEDED', 'advised_max': advised}
        return {'status': 'MATCHED'}

    return {'status': 'BLOCKED', 'code': 'OCCUPATION_SLOT_SCHEMA_UNSUPPORTED'}


def resolve_occupation_skill_choices(
    *,
    occupation_record: dict,
    selections: list[dict],
    characteristics: dict,
    era: str,
    keeper_authorized_mythos: bool = False,
) -> dict:
    if not isinstance(keeper_authorized_mythos, bool):
        return {'status': 'BLOCKED', 'code': 'KEEPER_MYTHOS_AUTH_FLAG_INVALID'}
    audit = occupation_slot_schema_audit()
    if audit['status'] != 'PASS':
        return {'status': 'BLOCKED', 'code': 'OCCUPATION_REGISTRY_SLOT_SCHEMA_AUDIT_FAILED', 'audit': audit}
    if not isinstance(occupation_record, dict) or not isinstance(occupation_record.get('skill_slots'), list):
        return {'status': 'BLOCKED', 'code': 'OCCUPATION_RECORD_INVALID'}
    slots = _expanded_slots(occupation_record)
    if len(slots) != 8 or not isinstance(selections, list) or len(selections) != 8:
        return {'status': 'BLOCKED', 'code': 'EXACTLY_EIGHT_OCCUPATION_SKILL_SELECTIONS_REQUIRED'}

    resolved = []
    seen = set()
    for flat_index, (slot_info, selection) in enumerate(zip(slots, selections)):
        if not isinstance(selection, dict):
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_SELECTION_INVALID', 'slot_index': flat_index}
        if selection.get('slot_index') != flat_index:
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_SELECTION_SLOT_INDEX_MISMATCH', 'slot_index': flat_index}
        points = selection.get('points', 0)
        if not _valid_int(points, 0):
            return {'status': 'BLOCKED', 'code': 'OCCUPATION_SKILL_POINTS_INVALID', 'slot_index': flat_index}
        match = _slot_matches(slot_info['slot'], selection, keeper_authorized_mythos=keeper_authorized_mythos)
        if match['status'] != 'MATCHED':
            return {**match, 'slot_index': flat_index}
        skill = _resolve_skill_record(selection['skill_id'], selection.get('specialization'), characteristics=characteristics, era=era)
        if skill['status'] != 'RESOLVED':
            return {**skill, 'slot_index': flat_index}
        if skill['canonical_key'] in seen:
            return {'status': 'BLOCKED', 'code': 'DUPLICATE_OCCUPATION_SKILL_SELECTION', 'skill_key': skill['canonical_key']}
        seen.add(skill['canonical_key'])
        resolved.append({
            'slot_index': flat_index,
            'source_slot_index': slot_info['source_slot_index'],
            'skill': skill,
            'points': points,
        })
    return {'status': 'RESOLVED', 'selections': resolved, 'automatic_skill_selection': False, 'automatic_specialization_selection': False}


def allocate_skills(
    *,
    batch1_preflight: dict,
    occupation_selections: list[dict],
    personal_interest_allocations: list[dict],
    era: str,
    keeper_authorized_mythos: bool = False,
) -> dict:
    if not isinstance(batch1_preflight, dict) or batch1_preflight.get('status') != 'READY_FOR_SKILL_ALLOCATION_BATCH2':
        return {'status': 'BLOCKED', 'code': 'BATCH1_PREFLIGHT_REQUIRED'}
    characteristics = batch1_preflight['aged']['characteristics']
    budgets = batch1_preflight['budgets']
    occupation_record = budgets['occupation_record']
    choices = resolve_occupation_skill_choices(
        occupation_record=occupation_record,
        selections=occupation_selections,
        characteristics=characteristics,
        era=era,
        keeper_authorized_mythos=keeper_authorized_mythos,
    )
    if choices['status'] != 'RESOLVED':
        return choices

    occupation_budget = budgets['occupation_points_remaining_after_credit_rating']
    occupation_spent = sum(x['points'] for x in choices['selections'])
    if occupation_spent > occupation_budget:
        return {'status': 'BLOCKED', 'code': 'OCCUPATION_ALLOCATION_EXCEEDS_BUDGET', 'budget': occupation_budget, 'spent': occupation_spent}

    skills = {}
    def ensure_skill(skill: dict):
        key = skill['canonical_key']
        if key not in skills:
            skills[key] = {
                'skill_id': skill['skill_id'],
                'specialization': skill['specialization'],
                'registry_skill_id': skill['registry_skill_id'],
                'base': skill['base'],
                'occupation_points': 0,
                'personal_interest_points': 0,
            }
        return skills[key]

    for item in choices['selections']:
        entry = ensure_skill(item['skill'])
        entry['occupation_points'] += item['points']

    if not isinstance(personal_interest_allocations, list):
        return {'status': 'BLOCKED', 'code': 'PERSONAL_INTEREST_ALLOCATIONS_INVALID'}
    personal_spent = 0
    for index, item in enumerate(personal_interest_allocations):
        if not isinstance(item, dict) or not {'skill_id', 'points'} <= set(item):
            return {'status': 'BLOCKED', 'code': 'PERSONAL_INTEREST_ENTRY_INVALID', 'entry_index': index}
        points = item['points']
        if not _valid_int(points, 0):
            return {'status': 'BLOCKED', 'code': 'PERSONAL_INTEREST_POINTS_INVALID', 'entry_index': index}
        sid = _norm(item['skill_id'])
        if sid == 'CTHULHU_MYTHOS' and not keeper_authorized_mythos:
            return {'status': 'BLOCKED', 'code': 'CTHULHU_MYTHOS_PERSONAL_INTEREST_REQUIRES_KEEPER_AUTHORIZATION'}
        skill = _resolve_skill_record(item['skill_id'], item.get('specialization'), characteristics=characteristics, era=era)
        if skill['status'] != 'RESOLVED':
            return {**skill, 'entry_index': index}
        entry = ensure_skill(skill)
        entry['personal_interest_points'] += points
        personal_spent += points

    personal_budget = budgets['personal_interest_points_total']
    if personal_spent > personal_budget:
        return {'status': 'BLOCKED', 'code': 'PERSONAL_INTEREST_ALLOCATION_EXCEEDS_BUDGET', 'budget': personal_budget, 'spent': personal_spent}

    for entry in skills.values():
        total = entry['base'] + entry['occupation_points'] + entry['personal_interest_points']
        entry['full'] = total
        entry['half'] = total // 2
        entry['fifth'] = total // 5

    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'skills': skills,
        'credit_rating': budgets['credit_rating_selected'],
        'occupation_budget': occupation_budget,
        'occupation_spent': occupation_spent,
        'occupation_points_lost_unspent': occupation_budget - occupation_spent,
        'personal_interest_budget': personal_budget,
        'personal_interest_spent': personal_spent,
        'personal_interest_points_lost_unspent': personal_budget - personal_spent,
        'automatic_skill_selection': False,
        'automatic_specialization_selection': False,
        'randomness_generated': False,
    }


def validate_backstory(*, identity: dict, backstory: dict, key_connection: dict) -> dict:
    if not isinstance(identity, dict) or set(identity) != {'name', 'gender', 'birthplace'}:
        return {'status': 'BLOCKED', 'code': 'IDENTITY_FIELDS_REQUIRED'}
    normalized_identity = {}
    for field in ('name', 'gender', 'birthplace'):
        value = identity[field]
        if not isinstance(value, str) or not value.strip():
            return {'status': 'BLOCKED', 'code': 'IDENTITY_FIELD_EMPTY', 'field': field}
        normalized_identity[field] = value.strip()

    if not isinstance(backstory, dict):
        return {'status': 'BLOCKED', 'code': 'BACKSTORY_INVALID'}
    allowed = set(REQUIRED_BACKSTORY) | set(OPTIONAL_BACKSTORY)
    normalized = {}
    for category, entries in backstory.items():
        key = _norm(category)
        if key not in allowed:
            return {'status': 'BLOCKED', 'code': 'BACKSTORY_CATEGORY_UNSUPPORTED', 'category': key}
        if isinstance(entries, str):
            entries = [entries]
        if not isinstance(entries, list) or not entries or any(not isinstance(v, str) or not v.strip() for v in entries):
            return {'status': 'BLOCKED', 'code': 'BACKSTORY_ENTRY_INVALID', 'category': key}
        normalized[key] = [v.strip() for v in entries]
    missing = [key for key in REQUIRED_BACKSTORY if key not in normalized]
    if missing:
        return {'status': 'BLOCKED', 'code': 'BACKSTORY_REQUIRED_CATEGORY_MISSING', 'missing': missing}

    if not isinstance(key_connection, dict) or set(key_connection) != {'category', 'entry_index'}:
        return {'status': 'BLOCKED', 'code': 'KEY_CONNECTION_REFERENCE_INVALID'}
    category = _norm(key_connection['category'])
    index = key_connection['entry_index']
    if category not in normalized or not _valid_int(index, 0) or index >= len(normalized[category]):
        return {'status': 'BLOCKED', 'code': 'KEY_CONNECTION_NOT_PRESENT_IN_BACKSTORY'}

    return {
        'status': 'RESOLVED',
        'identity': normalized_identity,
        'backstory': normalized,
        'key_connection': {'category': category, 'entry_index': index, 'text': normalized[category][index]},
        'automatic_backstory_generation': False,
        'automatic_key_connection_selection': False,
    }


def creation_batch2_preflight(
    *,
    batch1_preflight: dict,
    occupation_selections: list[dict],
    personal_interest_allocations: list[dict],
    era: str,
    identity: dict,
    backstory: dict,
    key_connection: dict,
    keeper_authorized_mythos: bool = False,
) -> dict:
    allocation = allocate_skills(
        batch1_preflight=batch1_preflight,
        occupation_selections=occupation_selections,
        personal_interest_allocations=personal_interest_allocations,
        era=era,
        keeper_authorized_mythos=keeper_authorized_mythos,
    )
    if allocation['status'] != 'RESOLVED':
        return {**allocation, 'creation_stage': 'SKILL_ALLOCATION'}
    story = validate_backstory(identity=identity, backstory=backstory, key_connection=key_connection)
    if story['status'] != 'RESOLVED':
        return {**story, 'creation_stage': 'BACKSTORY'}
    return {
        'status': 'READY_FOR_EQUIPMENT_FINANCE_BATCH3',
        'module_id': MODULE_ID,
        'batch1_preflight': copy.deepcopy(batch1_preflight),
        'skill_allocation': allocation,
        'story': story,
        'character_state_committed': False,
        'next_stage': 'EQUIPMENT_FINANCE_AND_ATOMIC_COMMIT_BATCH3',
        'randomness_generated': False,
        'authority_promoted': False,
    }
