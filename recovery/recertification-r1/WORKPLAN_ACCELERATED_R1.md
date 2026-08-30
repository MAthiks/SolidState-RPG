# Solid State RPG — Accelerated Production Workplan R1

Status: `WORKPLAN_ACTIVE_NOT_AUTHORITY`

Date: 2026-08-30

Authority floor: Checkpoint 333 — `MULTIPLAYER_FULL_STACK_RELEASE_AUDIT_V2`

Current frozen recovery candidate: `R1-C4B_MAISON`

This workplan changes development cadence only. It does not create Checkpoint 334, does not promote Recovery R1, does not alter the anti-rollback floor, and does not authorize embedding private/commercial PDFs.

## 1. Production objective

Accelerate Solid State RPG development while preserving:
- source-faithful Call of Cthulhu 7e mechanics;
- Keeper/Player knowledge isolation;
- actor-bound multiplayer state ownership;
- authenticated save/resume and Strict Replay;
- fail-closed behavior for unresolved rules or scenario sources;
- immutable frozen candidates and anti-rollback checkpoints.

## 2. Three-speed validation model

### DEV
Use targeted unit/integration tests for the modified component only.
- No full-chain rebuild for every small change.
- No package SHA freeze for intermediate work.
- No global scenario matrix unless the change touches shared runtime behavior.

### MODULE READY
When a functional module is complete, run its full module matrix.
Examples:
- one scenario x 1–4 players;
- one registry batch;
- one replay/save subsystem.

### RELEASE CANDIDATE
Only before promotion:
- rebuild the full recovery chain;
- run the complete non-regression matrix;
- verify anti-spoiler, source gates, ownership, save/resume, replay and tamper rejection;
- generate deterministic packages and freeze SHA-256 identities;
- decide whether a new checkpoint may be created.

## 3. Generic scenario pipeline

Every new or migrated scenario should use the same contract:

`SCENARIO_MANIFEST -> SOURCE_GATE -> CANONICAL_GRAPH -> PLAYER_PROJECTION -> STATE_BINDING -> MODULE_TEST_MATRIX`

The runtime should remain generic. Scenario-specific work should be represented primarily as structured, source-backed data and graph metadata rather than new bespoke runtime code.

Required scenario properties:
- scenario ID and edition;
- exact private source identity/hash gate;
- Gardien/Joueur source mode;
- canonical graph with optional branches preserved;
- no forced clue order unless the source requires it;
- player-safe projection;
- save binding to scenario ID, source hashes and canonical graph identity;
- restore-time revalidation;
- 1–4 player module matrix where supported.

## 4. Immediate scenario priority — Soleil Noir v1.7

The next scenario gate is `R1-C4B2`.

Target runtime edition: `Le Soleil Noir de Tobrouk v1.7`.

Important rule: v1.5/v1.6 remain provenance/history only and must not be silently selected as the active runtime edition.

Before compilation, v1.7 must receive explicit source identity materialization (Gardien/Joueur hashes). Until that gate passes, the runtime must fail closed rather than reuse the v1.5 source pair.

C4B2 work order:
1. materialize v1.7 Gardien/Joueur source identities;
2. create the v1.7 scenario manifest;
3. compile its canonical graph;
4. bind Gardien/Joueur projections;
5. bind world state and character knowledge partitions;
6. test 1–4 players;
7. test save/resume and Strict Replay;
8. test route/source tampering rejection;
9. run the Soleil Noir module matrix;
10. freeze C4B2 only after module completion.

## 5. CoC7 registry production in parallel

Rules registries should be data-driven and migrated in batches rather than encoded record-by-record in runtime logic.

Target structured registries:
- `skills.json`
- `occupations.json`
- `equipment.json`
- `weapons.json`

Each record should contain:
- stable record ID;
- normalized name;
- mechanical values/formulas;
- source ID;
- page/provenance reference where allowed;
- verification status;
- dependency information;
- `VERIFIED` or `BLOCKED` state.

Unverified records remain fail-closed.

## 6. Two parallel production lanes

### Lane A — Scenarios
1. Soleil Noir v1.7
2. normalize existing ROUTE_READY scenarios to the generic scenario contract
3. extend the official scenario registry
4. run scenario module matrices

### Lane B — CoC7 Rules
1. occupations batch expansion
2. skills completion/normalization
3. equipment expansion
4. weapons expansion
5. remaining core mechanics
6. rules package module matrices

The two lanes merge only at Release Candidate recertification unless a shared runtime dependency requires earlier integration.

## 7. Freeze discipline

Do not generate a new frozen ZIP for every sub-step.

A deterministic package and SHA-256 identity are generated only when a stage reaches:

`FROZEN_CANDIDATE`

Frozen ancestors are never rewritten. Corrections are carried by a new child stage.

## 8. Branch and commit discipline

Default working branch for the current recovery generation:
`recovery/recertification-r1`

Recommended unit of work:
`1 functional task -> 1 coherent change set -> targeted tests -> module validation`

Avoid unnecessary micro-commits whose only purpose is repeatedly freezing intermediate state.

## 9. Release path

Current sequence:

`Checkpoint333 authority`
-> `R1-C4B Maison frozen`
-> `R1-C4B2 Soleil Noir v1.7`
-> `CoC7 registry expansion in parallel`
-> `scenario pipeline normalization`
-> `full non-regression matrix`
-> `Recovery R1 Release Candidate`
-> `promotion decision / possible new checkpoint`
-> `Android integration`

Android promotion remains blocked until Recovery R1 is promoted by an explicit release audit.

## 10. Definition of Done for a module

A module is MODULE READY only if:
- required sources are verified;
- public tests pass;
- private/source-backed tests pass where required;
- player projection leaks = 0;
- wrong actor / invalid mutation / tampering fails closed;
- save/resume preserves canonical state;
- Strict Replay does not reroll recorded dice;
- scope limits are explicitly documented;
- no private/commercial source content is embedded in public artifacts.

## 11. Promotion invariant

Conversation memory never outranks verified artifacts.

Checkpoint 333 remains the authority until a later checkpoint is explicitly validated and promoted. Recovery R1 working plans and frozen candidates are not authority by themselves.
