from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'development' / 'r1-coc7-canonical-runtime-creation-binding'
PARENT_RUNNER = ROOT / 'development' / 'r1-coc7-investigator-creation-batch4' / 'run_hardened_gate.py'
PARENT_EXPECTED = 2714
TARGETED_EXPECTED = 100
COMBINED_EXPECTED = 2814


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
    if '"combined_tests": 2714' not in parent or '"result": "PASS"' not in parent:
        print(parent)
        fail('hardened creation Batch4 2714/2714 not proven')

    targeted = run([sys.executable, '-m', 'unittest', '-v', 'test_canonical_runtime_creation_binding_dev.py'], BATCH)
    if 'Ran 100 tests' not in targeted or '\nOK' not in targeted:
        print(targeted)
        fail('canonical runtime creation binding exact 100/100 not proven')

    c = json.loads((BATCH / 'canonical_runtime_creation_binding_contract.json').read_text())
    r = json.loads((BATCH / 'CANONICAL_RUNTIME_CREATION_BINDING_DEV_REPORT.json').read_text())
    assert c['schema'] == 'COC7_CANONICAL_RUNTIME_CREATION_BINDING_CONTRACT_V1'
    assert c['status'] == 'DEV_SOURCE_GROUNDED_NOT_FROZEN'
    assert c['module_id'] == 'COC7_CANONICAL_RUNTIME_CREATION_BINDING_R1_DEV_V1'
    assert c['parent_validated_commit'] == '3dc2b82b5a1ea2bb4f0e76694f3d8e8f26990154'
    assert c['parent_validated_proof'] == PARENT_EXPECTED
    assert c['frozen_runtime_integration_id'] == 'SOLIDSTATE_RECOVERY_RUNTIME_R1_C4_V1'
    assert c['checkpoint_floor'] == 333
    assert c['automatic_scenario_binding'] is False
    assert c['automatic_investigator_completion'] is False
    assert c['private_pdf_embedded'] is False
    assert c['authority_promoted'] is False
    assert c['checkpoint_created'] is False

    assert r['schema'] == 'COC7_CANONICAL_RUNTIME_CREATION_BINDING_DEV_REPORT_V1'
    assert r['module_id'] == c['module_id']
    assert r['status'] == 'DEV_VALIDATED_NOT_AUTHORITY'
    assert r['result'] == 'PASS'
    assert r['public_source_commit_tested'] == '6fb5b0a8f41383f09ef480a8e5161290b32cad92'
    assert r['github_actions_run_id'] == 33314356642
    assert r['parent_hardened_creation'] == {'passed': PARENT_EXPECTED, 'total': PARENT_EXPECTED}
    assert r['public_binding_tests'] == {'passed': TARGETED_EXPECTED, 'total': TARGETED_EXPECTED}
    assert r['combined_public_proof'] == {'passed': COMBINED_EXPECTED, 'total': COMBINED_EXPECTED}
    assert r['frozen_c4_package_sha256'] == 'e719a9295e088e48c23eec0d698d046045dd8f6dfa0e5713aa05cd53b114cb1b'
    assert r['rules_package_sha256'] == 'c18ad9763b44eb0d2864bc61ab01aa709eda604f4318af8498e6759df8f4b8c2'
    private = r['private_source_preflight']
    assert private['result'] == 'PASS'
    assert private['source_identities_verified'] == private['source_identities_total'] == 8
    assert private['canonical_session_cases'] == {'passed': 16, 'total': 16}
    assert private['save_restore_strict'] == {'passed': 16, 'total': 16}
    assert private['strict_replay_match'] == {'passed': 16, 'total': 16}
    assert private['player_projection_canonical_path_leaks'] == 0
    assert private['player_projection_source_hash_leaks'] == 0
    assert private['soleil_noir_blocked_as_path_uncompiled'] is True
    assert private['maison_pendu_blocked_as_source_unverified'] is True
    assert r['private_full_creation_end_to_end_completed'] is False
    assert r['automatic_scenario_binding'] is False
    assert r['private_pdf_embedded'] is False
    assert r['authority_promoted'] is False
    assert r['checkpoint_created'] is False

    tracked = run(['git', 'ls-files', 'development/r1-coc7-canonical-runtime-creation-binding'])
    if any(line.lower().endswith('.pdf') for line in tracked.splitlines()):
        fail('private PDF tracked in canonical runtime creation binding')

    print(json.dumps({
        'schema': 'COC7_CANONICAL_RUNTIME_CREATION_BINDING_HARDENED_GATE_V1',
        'result': 'PASS',
        'parent_tests': PARENT_EXPECTED,
        'targeted_tests': TARGETED_EXPECTED,
        'combined_tests': COMBINED_EXPECTED,
        'private_source_preflight_cases': 16,
        'authority_promoted': False,
        'checkpoint_created': False,
    }, indent=2))


if __name__ == '__main__':
    main()
