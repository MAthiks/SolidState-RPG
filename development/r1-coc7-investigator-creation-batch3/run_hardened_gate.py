from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'development' / 'r1-coc7-investigator-creation-batch3'
PARENT_RUNNER = ROOT / 'development' / 'r1-coc7-investigator-creation-batch2' / 'run_hardened_gate.py'
PARENT_EXPECTED = 2514
TARGETED_EXPECTED = 100
COMBINED_EXPECTED = 2614


def fail(message: str) -> None:
    raise SystemExit(message)


def run(cmd: list[str], cwd: Path = ROOT) -> str:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    out = (p.stdout or '') + (p.stderr or '')
    if p.returncode != 0:
        print(out)
        fail(f'command failed: {cmd!r}')
    return out


def main() -> None:
    parent = run([sys.executable, str(PARENT_RUNNER)])
    if '"combined_tests": 2514' not in parent or '"result": "PASS"' not in parent:
        print(parent)
        fail('hardened creation Batch2 2514/2514 not proven')

    targeted = run([sys.executable, '-m', 'unittest', '-v', 'test_investigator_creation_batch3_dev.py'], BATCH)
    if 'Ran 100 tests' not in targeted or '\nOK' not in targeted:
        print(targeted)
        fail('creation Batch3 exact 100/100 not proven')

    c = json.loads((BATCH / 'investigator_creation_batch3_contract.json').read_text())
    r = json.loads((BATCH / 'INVESTIGATOR_CREATION_BATCH3_DEV_REPORT.json').read_text())
    assert c['schema'] == 'COC7_INVESTIGATOR_CREATION_BATCH3_CONTRACT_V1'
    assert c['status'] == 'DEV_SOURCE_GROUNDED_NOT_FROZEN'
    assert c['module_id'] == 'COC7_INVESTIGATOR_CREATION_R1_BATCH3_DEV_V1'
    assert c['parent_validated_commit'] == 'a76d6d176209c110b25069a6e359b77d11422ed5'
    assert c['parent_validated_proof'] == PARENT_EXPECTED
    assert c['automatic_equipment_selection'] is False
    assert c['automatic_weapon_selection'] is False
    assert c['automatic_asset_conversion'] is False
    assert c['automatic_debt_creation'] is False
    assert c['random_values_generated_by_module'] is False
    assert c['private_cash_assets_table_embedded'] is False
    assert c['private_pdf_embedded'] is False
    assert c['authority_promoted'] is False
    assert c['checkpoint_created'] is False

    assert r['schema'] == 'COC7_INVESTIGATOR_CREATION_BATCH3_DEV_REPORT_V1'
    assert r['module_id'] == c['module_id']
    assert r['status'] == 'DEV_VALIDATED_NOT_AUTHORITY'
    assert r['result'] == 'PASS'
    assert r['source_commit_tested'] == '61cb5365f00cd635303ead732b9cd7b5cc2578da'
    assert r['github_actions_run_id'] == 33313199335
    assert r['parent_hardened_creation'] == {'passed': PARENT_EXPECTED, 'total': PARENT_EXPECTED}
    assert r['targeted_tests'] == {'passed': TARGETED_EXPECTED, 'total': TARGETED_EXPECTED}
    assert r['combined_proof'] == {'passed': COMBINED_EXPECTED, 'total': COMBINED_EXPECTED}
    assert r['actor_bound_atomic_commit_verified'] is True
    assert r['wrong_actor_zero_mutation_verified'] is True
    assert r['duplicate_creation_zero_mutation_verified'] is True
    assert r['one_to_four_players_verified'] is True
    assert r['initial_character_replay_baseline_updated'] is True
    assert r['save_restore_after_creation_verified'] is True
    assert r['strict_replay_after_creation_verified'] is True
    assert r['automatic_possession'] is False
    assert r['commercial_cash_assets_table_embedded'] is False
    assert r['private_pdf_embedded'] is False
    assert r['authority_promoted'] is False
    assert r['checkpoint_created'] is False
    assert r['next_stage'] == 'CANONICAL_SOURCE_BACKED_RUNTIME_CREATION_BINDING'

    tracked = run(['git', 'ls-files', 'development/r1-coc7-investigator-creation-batch3'])
    if any(line.lower().endswith('.pdf') for line in tracked.splitlines()):
        fail('private PDF tracked in investigator creation Batch3')

    print(json.dumps({
        'schema': 'COC7_INVESTIGATOR_CREATION_BATCH3_HARDENED_GATE_V1',
        'result': 'PASS',
        'parent_tests': PARENT_EXPECTED,
        'targeted_tests': TARGETED_EXPECTED,
        'combined_tests': COMBINED_EXPECTED,
        'atomic_creation_commit': True,
        'authority_promoted': False,
        'checkpoint_created': False,
    }, indent=2))


if __name__ == '__main__':
    main()
