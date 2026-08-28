# SOLID STATE — INTEGRATION PACKAGE 003
## Target: v7.8-RC1

Status: MIGRATION_PACKAGE
Baseline protected: Solid State v7.7 + CoC7 Rules Core v4.7
Purpose: merge the validated Startup Gate and Character Creation specifications into one controlled integration plan.

IMPORTANT
This package does NOT claim the canonical engine has already been modified.
It is the authoritative migration plan to apply once the verified companion Working Backup is physically available.

## REQUIRED INPUT
- Solid_State_v7.7_CoC7_v4.7_Working_Backup.zip
- SHA-256 expected:
  2adedf1049a24b1a84ad719c93110914054b0494f774be995cc8e9e5555ad2fe

If the Working Backup is absent or hash mismatch:
STOP -> VERSION NON CONFIRMÉE -> DO NOT INTEGRATE.

## INTEGRATION ORDER

### PHASE A — STARTUP GATE
Apply SSR-STARTUP-GATE-001A through 001G:
1. BOOT + menu
2. scenario selection
3. player count 1/2/3/4
4. Character Gate slots
5. per-player assistance mode
6. Preflight Gate
7. Ironman minimal save
8. ScenarioPresentationProfile

Blocking invariant:
SCENARIO_START remains LOCKED until every required Startup/Preflight condition passes.

### PHASE B — CHARACTER CREATION
Apply SSR-CHARACTER-CREATION-002A through 002E:
1. Source Gate
2. creation workflow
3. OccupationRegistry + SkillRegistry
4. Character Validator
5. DiceProvider

Blocking invariant:
No PENDING character may satisfy Character Gate.

### PHASE C — IMPORT HISTORY BOOLEAN
Scenario-level:
ALLOW_CHARACTER_HISTORY_STATE = true/false

false:
- durable profile only
true:
- compatible prior campaign state allowed

### PHASE D — PLAYER ASSISTANCE
Per player:
NORMAL/LIBRE default
ASSISTED optional on demand

Assisted suggestions:
3 contextual suggestions + 1 free action
PLAYER_KNOWLEDGE_ONLY
never Keeper secrets / hidden clues / future events / unknown solutions.

### PHASE E — IRONMAN SAVE
IRONMAN_MODE = true
ROLLBACK_FOR_GAMEPLAY = FORBIDDEN
ROLLBACK_FOR_TECHNICAL_RECOVERY = ALLOWED

SAVE_SLOT_0 = technical initial state
AUTOSAVE = progressive current state
MANUAL_SAVE = safety copy of current state
No gameplay rewind.

Committed dice rolls are immutable and persisted.

## REQUIRED REGRESSION TESTS BEFORE v7.8-RC1 CLAIM

STARTUP
- loaded scenario does not auto-start
- New Game cannot bypass player count
- New Game cannot bypass character creation/import
- Continue with no save reports cleanly
- Diagnostic never starts narration
- Scenario Start remains locked on any critical Preflight failure

CHARACTER CREATION
- French archaeologist resolves canonically
- pilot creation reaches READY
- wrong occupation total -> PENDING
- Credit Rating outside range -> PENDING
- required skill missing -> PENDING
- wrong personal total -> PENDING
- interrupted creation -> PENDING

MULTIPLAYER
- 2-player transaction isolation
- 4-player transaction isolation
- one PENDING slot locks Character Gate
- fixing one transaction does not alter others

IRONMAN
- committed roll cannot be rerolled by reload
- death/injury/missed clue cannot be undone through normal load
- technical recovery may restore latest valid compatible state only

DOCUMENTARY
- missing required source blocks affected operation
- README/chat claims never substitute actual source accessibility
- Keeper/Player knowledge remains partitioned

## RELEASE GATE
Only after all mandatory tests pass:
- declare v7.8-RC1 IMPLEMENTED
- create new Working Backup
- compute SHA-256
- create Work Checkpoint
- then continue to next feature.

## TECHNICAL ROLLBACK
If integration corrupts the candidate:
1. STOP
2. discard candidate only
3. restore verified v7.7 Working Backup
4. verify its SHA-256
5. reapply only previously verified migration steps
6. never overwrite the protected baseline
