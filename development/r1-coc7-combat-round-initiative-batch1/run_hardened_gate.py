from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'development' / 'r1-coc7-combat-round-initiative-batch1'

PARENT_EXPECTED = 1456
TARGETED_EXPECTED = 72
COMBINED_EXPECTED = 1528

TESTS = [
    ('development/r1-coc7-equipment-weapons-batch1', 'test_eqwp_batch1_dev.py', 173),
    ('development/r1-coc7-combat-firearms-batch1', 'test_combat_firearms_dev.py', 55),
    ('development/r1-coc7-combat-firearms-batch2', 'test_combat_firearms_batch2_dev.py', 79),
    ('development/r1-coc7-melee-combat-batch1', 'test_melee_combat_dev.py', 65),
    ('development/r1-coc7-wounds-healing-batch1', 'test_wounds_healing_dev.py', 98),
    ('development/r1-coc7-sanity-insanity-batch1', 'test_sanity_insanity_dev.py', 80),
    ('development/r1-coc7-sanity-treatment-batch2', 'test_sanity_treatment_dev.py', 75),
    ('development/r1-coc7-chase-batch1', 'test_chase_dev.py', 70),
    ('development/r1-coc7-chase-batch2', 'test_chase_batch2_dev.py', 84),
    ('development/r1-coc7-magic-core-batch1', 'test_magic_core_dev.py', 96),
    ('development/r1-coc7-magic-core-batch2', 'test_magic_core_batch2_dev.py', 75),
    ('development/r1-coc7-investigator-development-batch1', 'test_investigator_development_dev.py', 92),
    ('development/r1-coc7-investigator-aging-batch2', 'test_investigator_aging_dev.py', 94),
    ('development/r1-coc7-finance-credit-rating-batch1', 'test_finance_credit_rating_dev.py', 99),
    ('development/r1-coc7-general-skill-resolution-batch1', 'test_general_skill_resolution_dev.py', 104),
    ('development/r1-coc7-luck-spending-batch1', 'test_luck_spending_dev.py', 80),
    ('development/r1-coc7-combat-round-initiative-batch1', 'test_combat_round_initiative_dev.py', 72),
]


def fail(message: str) -> None:
    raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> str:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    output = (p.stdout or '') + (p.stderr or '')
    if p.returncode != 0:
        print(output)
        fail(f'command failed ({p.returncode}): {cmd!r}')
    return output


def verify_rules_core() -> int:
    out = run([sys.executable, '-m', 'rules_r1.test_core_rules'], ROOT / 'recovery' / 'recertification-r1')
    if not re.search(r'"passed"\s*:\s*37', out) or not re.search(r'"total"\s*:\s*37', out):
        print(out)
        fail('Rules Core exact 37/37 count not proven')
    return 37


def verify_unittest(dir_rel: str, filename: str, expected: int) -> int:
    out = run([sys.executable, '-m', 'unittest', '-v', filename], ROOT / dir_rel)
    if f'Ran {expected} tests' not in out or '\nOK' not in out:
        print(out)
        fail(f'exact test count/result not proven for {dir_rel}: expected {expected}')
    print(f'PASS {dir_rel}: {expected}/{expected}')
    return expected


def verify_documents() -> None:
    contract = json.loads((BATCH / 'combat_round_initiative_batch1_contract.json').read_text())
    report = json.loads((BATCH / 'COMBAT_ROUND_INITIATIVE_BATCH1_DEV_REPORT.json').read_text())

    assert contract['schema'] == 'COC7_COMBAT_ROUND_INITIATIVE_BATCH1_CONTRACT_V1'
    assert contract['status'] == 'DEV_SOURCE_GROUNDED_NOT_FROZEN'
    assert contract['module_id'] == 'COC7_COMBAT_ROUND_INITIATIVE_R1_BATCH1_DEV_V1'
    assert contract['parent_luck_module_id'] == 'COC7_LUCK_SPENDING_R1_BATCH1_DEV_V1'
    assert contract['parent_validated_commit'] == '1d948322eb30078314e0e3fad0fcf80ee70989bf'
    assert contract['parent_validated_test_chain'] == PARENT_EXPECTED
    assert contract['source']['source_id'] == 'COC7_KEEPER'
    assert contract['source']['sha256'] == '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
    assert contract['source']['printed_pages'] == [102, 112]

    m = contract['materialized_rules']
    required_true = [
        'one_turn_opportunity_per_capable_willing_combatant_per_round',
        'base_order_highest_dex_first',
        'dex_tie_higher_combat_skill_first',
        'unresolved_exact_tie_fails_closed',
        'readied_firearm_shot_uses_dex_plus_50',
        'readied_firearm_bonus_reused_from_firearms_batch1',
        'monster_multiple_attacks_share_one_monster_turn',
        'character_may_delay_until_another_character_acts',
        'simultaneous_delayed_actions_use_highest_raw_dex',
        'simultaneous_delayed_raw_dex_tie_fails_closed',
        'mutual_wait_can_end_with_both_actions_lost_only_by_explicit_keeper_resolution',
        'round_completion_requires_every_declared_participant_to_be_nonpending',
    ]
    for key in required_true:
        assert m[key] is True, key

    reuse = contract['reuse_policy']
    assert reuse['firearm_dex_order_reused_from_combat_firearms_batch1'] is True
    assert reuse['duplicate_readied_firearm_bonus_engine_created'] is False
    assert reuse['combat_attack_resolution_not_duplicated'] is True
    assert reuse['melee_resolution_not_duplicated'] is True

    assert contract['automatic_action_selection'] is False
    assert contract['automatic_tie_break'] is False
    assert contract['automatic_round_end_on_mutual_wait'] is False
    assert contract['random_values_generated_by_module'] is False
    assert contract['private_pdf_embedded'] is False
    assert contract['authority_promoted'] is False
    assert contract['checkpoint_created'] is False

    assert report['schema'] == 'COC7_COMBAT_ROUND_INITIATIVE_BATCH1_DEV_REPORT_V1'
    assert report['module_id'] == contract['module_id']
    assert report['result'] == 'PASS'
    assert report['source_commit_tested'] == '0302b7dc7ce80ffb806f4201f597830644285e05'
    assert report['github_actions_run_id'] == 33308751347
    assert report['targeted_tests'] == {'passed': TARGETED_EXPECTED, 'total': TARGETED_EXPECTED}
    assert report['prior_validated_chain'] == {'passed': PARENT_EXPECTED, 'total': PARENT_EXPECTED}
    assert report['combined_chain'] == {'passed': COMBINED_EXPECTED, 'total': COMBINED_EXPECTED}
    assert report['source_grounded'] is True
    assert report['keeper_source_id'] == contract['source']['source_id']
    assert report['keeper_source_sha256'] == contract['source']['sha256']
    assert report['keeper_printed_pages'] == [102, 112]
    assert report['highest_dex_first'] is True
    assert report['dex_tie_higher_combat_skill_first'] is True
    assert report['exact_tie_fail_closed'] is True
    assert report['readied_firearm_dex_plus_50_reused'] is True
    assert report['monster_multiple_attacks_share_one_turn'] is True
    assert report['delayed_action_supported'] is True
    assert report['simultaneous_delayed_action_uses_raw_dex'] is True
    assert report['simultaneous_delay_tie_fail_closed'] is True
    assert report['mutual_wait_requires_explicit_keeper_resolution'] is True
    assert report['round_completion_requires_no_pending_declared_participant'] is True
    assert report['automatic_action_selection'] is False
    assert report['automatic_tie_break'] is False
    assert report['automatic_round_end_on_mutual_wait'] is False
    assert report['random_values_generated_by_module'] is False
    assert report['private_pdf_embedded'] is False
    assert report['authority_promoted'] is False
    assert report['checkpoint_created'] is False
    assert report['status'] == 'DEV_VALIDATED_NOT_AUTHORITY'


def verify_no_private_pdf() -> None:
    out = run(['git', 'ls-files', 'development/r1-coc7-combat-round-initiative-batch1'], ROOT)
    tracked = [line for line in out.splitlines() if line.lower().endswith('.pdf')]
    if tracked:
        fail(f'private PDF tracked in batch: {tracked}')


def main() -> None:
    total = verify_rules_core()
    for dir_rel, filename, expected in TESTS:
        total += verify_unittest(dir_rel, filename, expected)
    if sum([37] + [x[2] for x in TESTS[:-1]]) != PARENT_EXPECTED:
        fail('parent arithmetic mismatch')
    if total != COMBINED_EXPECTED:
        fail(f'combined arithmetic mismatch: {total} != {COMBINED_EXPECTED}')
    verify_documents()
    verify_no_private_pdf()
    print(json.dumps({
        'schema': 'COC7_COMBAT_ROUND_INITIATIVE_BATCH1_HARDENED_GATE_V1',
        'result': 'PASS',
        'prior_validated_chain': PARENT_EXPECTED,
        'targeted_tests': TARGETED_EXPECTED,
        'combined_tests': COMBINED_EXPECTED,
        'authority_promoted': False,
        'checkpoint_created': False,
    }, indent=2))


if __name__ == '__main__':
    main()
