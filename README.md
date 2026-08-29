# SolidState-RPG

Official version-controlled source of truth for the Solid State RPG project.

## Current development authority — Checkpoint 333 VERIFIED

- Checkpoint: `333`
- ID: `MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2`
- Parent: `332 — MULTIPLAYER_STRICT_REPLAY_RECERTIFICATION_V2`
- Record: `patches/checkpoint333/CHECKPOINT_333.json`
- Record Git blob SHA-1: `965695bdc3ebe13f7337bb491796f6a193bd8fa6`
- Combined source-backed matrix: `2300/2300 PASS`
- Exact Checkpoint 332 rerun: `558/558 PASS`
- Matrix: 5 `PASS_REAL` scenarios × 1–4 players = 20 core cases
- Keeper→Player leaks: `0`

## Multiplayer V2 release stack

Checkpoint 330 certifies independent player state/control/knowledge. Checkpoint 331 certifies authenticated, atomic multiplayer save/resume. Checkpoint 332 certifies actor-bound multiplayer Strict Replay. Checkpoint 333 release-audits all three layers together against the exact private source pack without publishing commercial source material.

The combined audit stresses interleaved actor-bound actions, Player/Keeper knowledge changes, failed actions with zero mutation, multiple save/resume cut positions, resumed Strict Replay equality, semantic SQL/canonical/player-view equality and tampering of authentication, checkpoint floor, control, ownership, knowledge and actor attribution.

Replay never rerolls a recorded value. Duplicate, omitted and reordered replay events remain rejected. Wrong-character and invalid-roll actions fail before commit. A deliberately re-attributed event whose hash chain is rebuilt remains detectable against the expected actor tape.

The inherited parent certifications remain authoritative: Checkpoint 331 `987/987 PASS`, Checkpoint 330 `522/522 PASS`. Checkpoint 333 does not falsely report those complete parent matrices as newly rerun; it verifies the exact parent module identities and reruns the exact Checkpoint 332 matrix `558/558 PASS` in addition to its own `2300/2300` combined audit.

## Scenario status

- scenario3 — Les Maudits: `PASS_REAL`, source-ready
- scenario4 — Les Registres de Brume: `PASS_REAL`, source-ready
- scenario5 — L'Antre de l'abomination: `PASS_REAL`, source-ready
- scenario6 — Muse équivoque aux yeux de sel gemme: `PASS_REAL`, source-ready
- scenario7 — L'Explorateur assassiné: `PASS_REAL`, source-ready

## Next phase

`ANDROID_RUNTIME_INTEGRATION_V1`

Android APK work may now resume, but only from the Checkpoint 333 certified runtime stack. No APK is promoted until runtime integration, signing and artifact verification pass their own release gate.

Automatic downgrade is forbidden.
