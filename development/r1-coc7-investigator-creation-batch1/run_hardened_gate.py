from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'development' / 'r1-coc7-investigator-creation-batch1'
RULES_PARENT = ROOT / 'development' / 'r1-coc7-other-forms-damage-batch1' / 'run_hardened_gate.py'
RULES_EXPECTED = 1688
REGISTRY_EXPECTED = 626
TARGETED_EXPECTED = 100
COMBINED_EXPECTED = 2414


def fail(message: str) -> None:
    raise SystemExit(message)


def run(cmd: list[str], cwd: Path = ROOT) -> str:
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    out = (p.stdout or '') + (p.stderr or '')
    if p.returncode != 0:
        print(out)
        fail(f'command failed: {cmd!r}')
    return out


def run_registry_batch(batch: int, expected: int) -> None:
    d = ROOT / 'development' / f'r1-coc7-registry-batch{batch}'
    out = run([sys.executable, '-m', 'unittest', 'discover', '-v', '-p', 'test_*_dev.py'], d)
    if f'Ran {expected} tests' not in out or '\nOK' not in out:
        print(out)
        fail(f'registry batch{batch} exact {expected} not proven')


def main() -> None:
    parent = run([sys.executable, str(RULES_PARENT)])
    if '"combined_tests": 1688' not in parent or '"result": "PASS"' not in parent:
        print(parent)
        fail('hardened rules parent 1688/1688 not proven')

    for batch, expected in [(1,50),(2,128),(3,128),(4,200),(5,120)]:
        run_registry_batch(batch, expected)

    targeted = run([sys.executable, '-m', 'unittest', '-v', 'test_investigator_creation_dev.py'], BATCH)
    if 'Ran 100 tests' not in targeted or '\nOK' not in targeted:
        print(targeted)
        fail('creation targeted exact 100/100 not proven')

    c = json.loads((BATCH / 'investigator_creation_batch1_contract.json').read_text())
    r = json.loads((BATCH / 'INVESTIGATOR_CREATION_BATCH1_DEV_REPORT.json').read_text())
    assert c['schema'] == 'COC7_INVESTIGATOR_CREATION_BATCH1_CONTRACT_V1'
    assert c['status'] == 'DEV_SOURCE_GROUNDED_NOT_FROZEN'
    assert c['module_id'] == 'COC7_INVESTIGATOR_CREATION_R1_BATCH1_DEV_V1'
    assert c['parent_rules_commit'] == 'da3cbd84575fd7533ec3e21e21fe07ceb4ac9b28'
    assert c['parent_rules_test_chain'] == RULES_EXPECTED
    assert c['occupation_registry_id'] == 'COC7_RECOVERY_REGISTRY_R1_BATCH5_DEV_V1'
    assert c['occupation_registry_test_chain'] == REGISTRY_EXPECTED
    assert c['sources']['investigator']['sha256'] == 'de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17'
    assert c['sources']['investigator']['printed_pages'] == [42,43,44,45,48,49,50]
    assert c['automatic_characteristic_reroll'] is False
    assert c['automatic_age_allocation'] is False
    assert c['automatic_occupation_selection'] is False
    assert c['automatic_credit_rating_selection'] is False
    assert c['random_values_generated_by_module'] is False
    assert c['private_pdf_embedded'] is False
    assert c['authority_promoted'] is False
    assert c['checkpoint_created'] is False

    assert r['schema'] == 'COC7_INVESTIGATOR_CREATION_BATCH1_DEV_REPORT_V1'
    assert r['module_id'] == c['module_id']
    assert r['result'] == 'PASS'
    assert r['status'] == 'DEV_VALIDATED_NOT_AUTHORITY'
    assert r['source_commit_tested'] == '22a4e6eafeab403de646817acb3683ea62e92aa6'
    assert r['github_actions_run_id'] == 33309896396
    assert r['rules_chain'] == {'passed':RULES_EXPECTED,'total':RULES_EXPECTED}
    assert r['occupation_registry_chain'] == {'passed':REGISTRY_EXPECTED,'total':REGISTRY_EXPECTED}
    assert r['targeted_tests'] == {'passed':TARGETED_EXPECTED,'total':TARGETED_EXPECTED}
    assert r['combined_proof'] == {'passed':COMBINED_EXPECTED,'total':COMBINED_EXPECTED}
    assert r['archaeologist_creation_preflight_verified'] is True
    assert r['character_state_committed'] is False
    assert r['next_stage'] == 'OCCUPATION_AND_PERSONAL_INTEREST_SKILL_ALLOCATION_BATCH2'
    assert r['random_values_generated_by_module'] is False
    assert r['private_pdf_embedded'] is False
    assert r['authority_promoted'] is False
    assert r['checkpoint_created'] is False

    tracked = run(['git', 'ls-files', 'development/r1-coc7-investigator-creation-batch1'])
    if any(line.lower().endswith('.pdf') for line in tracked.splitlines()):
        fail('private PDF tracked in investigator creation batch1')

    print(json.dumps({
        'schema': 'COC7_INVESTIGATOR_CREATION_BATCH1_HARDENED_GATE_V1',
        'result': 'PASS',
        'rules_tests': RULES_EXPECTED,
        'occupation_registry_tests': REGISTRY_EXPECTED,
        'targeted_tests': TARGETED_EXPECTED,
        'combined_tests': COMBINED_EXPECTED,
        'character_state_committed': False,
        'authority_promoted': False,
        'checkpoint_created': False,
    }, indent=2))


if __name__ == '__main__':
    main()
