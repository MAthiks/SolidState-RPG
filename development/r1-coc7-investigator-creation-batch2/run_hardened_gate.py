from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'development' / 'r1-coc7-investigator-creation-batch2'
PARENT_RUNNER = ROOT / 'development' / 'r1-coc7-investigator-creation-batch1' / 'run_hardened_gate.py'
PARENT_EXPECTED = 2414
TARGETED_EXPECTED = 100
COMBINED_EXPECTED = 2514
OCCUPATION_SCHEMA_COUNT = 114


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
    if '"combined_tests": 2414' not in parent or '"result": "PASS"' not in parent:
        print(parent)
        fail('hardened creation Batch1 2414/2414 not proven')

    audit = run([
        sys.executable, '-c',
        "import sys; from pathlib import Path; d=Path('development/r1-coc7-investigator-creation-batch2'); sys.path.insert(0,str(d)); import investigator_creation_batch2_dev as m; r=m.occupation_slot_schema_audit(); assert r['status']=='PASS',r; assert r['occupation_count']==114,r; print(r)"
    ])
    if "'occupation_count': 114" not in audit or "'status': 'PASS'" not in audit:
        print(audit)
        fail('occupation schema audit 114 not proven')

    targeted = run([sys.executable, '-m', 'unittest', '-v', 'test_investigator_creation_batch2_dev.py'], BATCH)
    if 'Ran 100 tests' not in targeted or '\nOK' not in targeted:
        print(targeted)
        fail('creation Batch2 exact 100/100 not proven')

    c = json.loads((BATCH / 'investigator_creation_batch2_contract.json').read_text())
    r = json.loads((BATCH / 'INVESTIGATOR_CREATION_BATCH2_DEV_REPORT.json').read_text())

    assert c['schema'] == 'COC7_INVESTIGATOR_CREATION_BATCH2_CONTRACT_V1'
    assert c['status'] == 'DEV_SOURCE_GROUNDED_NOT_FROZEN'
    assert c['module_id'] == 'COC7_INVESTIGATOR_CREATION_R1_BATCH2_DEV_V1'
    assert c['parent_validated_commit'] == '65fe598cda467611d0ab1eb06f3d4f51f0dce917'
    assert c['parent_validated_proof'] == PARENT_EXPECTED
    assert c['source']['sha256'] == 'de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17'
    assert c['automatic_skill_selection'] is False
    assert c['automatic_specialization_selection'] is False
    assert c['automatic_backstory_generation'] is False
    assert c['automatic_key_connection_selection'] is False
    assert c['random_values_generated_by_module'] is False
    assert c['character_state_committed'] is False
    assert c['private_pdf_embedded'] is False
    assert c['authority_promoted'] is False
    assert c['checkpoint_created'] is False

    assert r['schema'] == 'COC7_INVESTIGATOR_CREATION_BATCH2_DEV_REPORT_V1'
    assert r['module_id'] == c['module_id']
    assert r['status'] == 'DEV_VALIDATED_NOT_AUTHORITY'
    assert r['result'] == 'PASS'
    assert r['source_commit_tested'] == '396ce6a26dcbfda64bd6e0cc46b0a7fedb1a7508'
    assert r['github_actions_run_id'] == 33312751521
    assert r['parent_hardened_creation'] == {'passed': PARENT_EXPECTED, 'total': PARENT_EXPECTED}
    assert r['occupation_schemas_audited'] == OCCUPATION_SCHEMA_COUNT
    assert r['targeted_tests'] == {'passed': TARGETED_EXPECTED, 'total': TARGETED_EXPECTED}
    assert r['combined_proof'] == {'passed': COMBINED_EXPECTED, 'total': COMBINED_EXPECTED}
    assert r['all_occupation_slot_schemas_supported'] is True
    assert r['science_unmaterialized_specialization_fail_closed'] is True
    assert r['character_state_committed'] is False
    assert r['private_pdf_embedded'] is False
    assert r['authority_promoted'] is False
    assert r['checkpoint_created'] is False
    assert r['next_stage'] == 'EQUIPMENT_FINANCE_AND_ATOMIC_COMMIT_BATCH3'

    tracked = run(['git', 'ls-files', 'development/r1-coc7-investigator-creation-batch2'])
    if any(line.lower().endswith('.pdf') for line in tracked.splitlines()):
        fail('private PDF tracked in investigator creation Batch2')

    print(json.dumps({
        'schema': 'COC7_INVESTIGATOR_CREATION_BATCH2_HARDENED_GATE_V1',
        'result': 'PASS',
        'parent_tests': PARENT_EXPECTED,
        'occupation_schemas_audited': OCCUPATION_SCHEMA_COUNT,
        'targeted_tests': TARGETED_EXPECTED,
        'combined_tests': COMBINED_EXPECTED,
        'character_state_committed': False,
        'authority_promoted': False,
        'checkpoint_created': False,
    }, indent=2))


if __name__ == '__main__':
    main()
