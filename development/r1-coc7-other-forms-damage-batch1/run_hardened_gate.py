from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / 'development' / 'r1-coc7-other-forms-damage-batch1'
PARENT_RUNNER = ROOT / 'development' / 'r1-coc7-ranged-thrown-armor-batch1' / 'run_hardened_gate.py'
PARENT_EXPECTED = 1608
TARGETED_EXPECTED = 80
COMBINED_EXPECTED = 1688


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
    if '"combined_tests": 1608' not in parent or '"result": "PASS"' not in parent:
        print(parent)
        fail('hardened parent 1608/1608 not proven')

    targeted = run([sys.executable, '-m', 'unittest', '-v', 'test_other_forms_damage_dev.py'], BATCH)
    if 'Ran 80 tests' not in targeted or '\nOK' not in targeted:
        print(targeted)
        fail('targeted exact 80/80 not proven')

    c = json.loads((BATCH / 'other_forms_damage_batch1_contract.json').read_text())
    r = json.loads((BATCH / 'OTHER_FORMS_DAMAGE_BATCH1_DEV_REPORT.json').read_text())
    assert c['schema'] == 'COC7_OTHER_FORMS_DAMAGE_BATCH1_CONTRACT_V1'
    assert c['status'] == 'DEV_SOURCE_GROUNDED_NOT_FROZEN'
    assert c['module_id'] == 'COC7_OTHER_FORMS_DAMAGE_R1_BATCH1_DEV_V1'
    assert c['parent_ranged_thrown_armor_module_id'] == 'COC7_RANGED_THROWN_ARMOR_R1_BATCH1_DEV_V1'
    assert c['parent_validated_commit'] == '9815b353f3fa7c4ef01b34ab6019ed1675a6ecef'
    assert c['parent_validated_test_chain'] == PARENT_EXPECTED
    assert c['source']['source_id'] == 'COC7_KEEPER'
    assert c['source']['sha256'] == '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
    assert c['source']['printed_pages'] == [123, 124]
    assert c['automatic_severity_selection'] is False
    assert c['automatic_poison_symptom_selection'] is False
    assert c['random_values_generated_by_module'] is False
    assert c['private_pdf_embedded'] is False
    assert c['authority_promoted'] is False
    assert c['checkpoint_created'] is False

    assert r['schema'] == 'COC7_OTHER_FORMS_DAMAGE_BATCH1_DEV_REPORT_V1'
    assert r['module_id'] == c['module_id']
    assert r['result'] == 'PASS'
    assert r['source_commit_tested'] == 'e1572a8734368cc082e515ec9e2c36ba09e1dfa9'
    assert r['github_actions_run_id'] == 33309476311
    assert r['targeted_tests'] == {'passed': TARGETED_EXPECTED, 'total': TARGETED_EXPECTED}
    assert r['prior_validated_chain'] == {'passed': PARENT_EXPECTED, 'total': PARENT_EXPECTED}
    assert r['combined_chain'] == {'passed': COMBINED_EXPECTED, 'total': COMBINED_EXPECTED}
    assert r['source_grounded'] is True
    assert r['severity_profiles_materialized'] is True
    assert r['recorded_damage_dice_required'] is True
    assert r['repeated_exposure_materialized'] is True
    assert r['asphyxiation_drowning_materialized'] is True
    assert r['asphyxiation_zero_hp_death_ignores_major_wound'] is True
    assert r['poison_extreme_con_halving_materialized'] is True
    assert r['poison_critical_shakeoff_automatic'] is False
    assert r['poison_symptoms_automatic'] is False
    assert r['ordinary_wounds_engine_reused'] is True
    assert r['automatic_severity_selection'] is False
    assert r['random_values_generated_by_module'] is False
    assert r['private_pdf_embedded'] is False
    assert r['authority_promoted'] is False
    assert r['checkpoint_created'] is False
    assert r['status'] == 'DEV_VALIDATED_NOT_AUTHORITY'

    tracked = run(['git', 'ls-files', 'development/r1-coc7-other-forms-damage-batch1'])
    if any(line.lower().endswith('.pdf') for line in tracked.splitlines()):
        fail('private PDF tracked in other forms damage batch')

    print(json.dumps({
        'schema': 'COC7_OTHER_FORMS_DAMAGE_BATCH1_HARDENED_GATE_V1',
        'result': 'PASS',
        'prior_validated_chain': PARENT_EXPECTED,
        'targeted_tests': TARGETED_EXPECTED,
        'combined_tests': COMBINED_EXPECTED,
        'authority_promoted': False,
        'checkpoint_created': False,
    }, indent=2))


if __name__ == '__main__':
    main()
