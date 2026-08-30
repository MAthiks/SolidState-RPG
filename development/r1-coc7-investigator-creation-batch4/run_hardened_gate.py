from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'development' / 'r1-coc7-investigator-creation-batch4'
PARENT_RUNNER = ROOT / 'development' / 'r1-coc7-investigator-creation-batch3' / 'run_hardened_gate.py'
PARENT_EXPECTED = 2614
TARGETED_EXPECTED = 100
COMBINED_EXPECTED = 2714


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
    if '"combined_tests": 2614' not in parent or '"result": "PASS"' not in parent:
        print(parent)
        fail('hardened creation Batch3 2614/2614 not proven')

    targeted = run([sys.executable, '-m', 'unittest', '-v', 'test_investigator_creation_batch4_dev.py'], BATCH)
    if 'Ran 100 tests' not in targeted or '\nOK' not in targeted:
        print(targeted)
        fail('creation Batch4 exact 100/100 not proven')

    c = json.loads((BATCH / 'investigator_creation_batch4_contract.json').read_text())
    r = json.loads((BATCH / 'INVESTIGATOR_CREATION_BATCH4_DEV_REPORT.json').read_text())
    assert c['schema'] == 'COC7_INVESTIGATOR_CREATION_BATCH4_CONTRACT_V1'
    assert c['status'] == 'DEV_SOURCE_GROUNDED_NOT_FROZEN'
    assert c['module_id'] == 'COC7_INVESTIGATOR_CREATION_R1_BATCH4_DEV_V1'
    assert c['parent_validated_commit'] == 'e733100015ad5a565aedde7f622647eeac40dd94'
    assert c['parent_validated_proof'] == PARENT_EXPECTED
    assert c['checkpoint_floor'] == 333
    assert c['automatic_investigator_completion'] is False
    assert c['automatic_equipment_selection'] is False
    assert c['automatic_finance_selection'] is False
    assert c['random_values_generated_by_module'] is False
    assert c['private_pdf_embedded'] is False
    assert c['authority_promoted'] is False
    assert c['checkpoint_created'] is False

    assert r['schema'] == 'COC7_INVESTIGATOR_CREATION_BATCH4_DEV_REPORT_V1'
    assert r['module_id'] == c['module_id']
    assert r['status'] == 'DEV_VALIDATED_NOT_AUTHORITY'
    assert r['result'] == 'PASS'
    assert r['source_commit_tested'] == '9a1eee18e3d1d5f9c8b811e02d881c30ea4aa950'
    assert r['github_actions_run_id'] == 33313982020
    assert r['parent_hardened_creation'] == {'passed': PARENT_EXPECTED, 'total': PARENT_EXPECTED}
    assert r['targeted_tests'] == {'passed': TARGETED_EXPECTED, 'total': TARGETED_EXPECTED}
    assert r['combined_proof'] == {'passed': COMBINED_EXPECTED, 'total': COMBINED_EXPECTED}
    assert r['party_sizes_verified'] == [1, 2, 3, 4]
    assert r['independent_creation_transactions_verified'] is True
    assert r['incomplete_party_play_blocked_zero_mutation'] is True
    assert r['party_finalization_atomic'] is True
    assert r['play_ready_phase_bound'] is True
    assert r['roster_fingerprint_bound_to_initial_character_baselines'] is True
    assert r['wrong_actor_after_finalization_zero_mutation'] is True
    assert r['save_restore_after_party_finalization_verified'] is True
    assert r['strict_replay_after_party_finalization_verified'] is True
    assert r['automatic_investigator_completion'] is False
    assert r['private_pdf_embedded'] is False
    assert r['authority_promoted'] is False
    assert r['checkpoint_created'] is False
    assert r['next_stage'] == 'CANONICAL_SOURCE_BACKED_RUNTIME_CREATION_BINDING'

    tracked = run(['git', 'ls-files', 'development/r1-coc7-investigator-creation-batch4'])
    if any(line.lower().endswith('.pdf') for line in tracked.splitlines()):
        fail('private PDF tracked in investigator creation Batch4')

    print(json.dumps({
        'schema': 'COC7_INVESTIGATOR_CREATION_BATCH4_HARDENED_GATE_V1',
        'result': 'PASS',
        'parent_tests': PARENT_EXPECTED,
        'targeted_tests': TARGETED_EXPECTED,
        'combined_tests': COMBINED_EXPECTED,
        'party_creation_finalization': True,
        'authority_promoted': False,
        'checkpoint_created': False,
    }, indent=2))


if __name__ == '__main__':
    main()
