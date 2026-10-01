# Handover — Claude (cloud) → whoever picks this up next

Originally written 2026-09-29 at the end of the cloud session that ran Sessions 055–076 (with the local agents' sessions interleaved); current-status notes were reconciled 2026-10-01.

> **Current handoff note:** this is a historical cloud-session document, not the authoritative current task list. See `NEXT_PRIORITIES.md`, `PROJECT_AUDIT.md`, and current map/register documents first; old prompts and risk actions below are retained for context and may be superseded.
It's for the next Claude cloud session, or any agent taking over the work this session was doing. Read it after
`CLAUDE.md`. Everything here is either measured and committed, or marked as not verified.

> ## → Read `Docs/NEXT_PRIORITIES.md` first for what to build
>
> §1–§6 of this file describe **the state of one cloud session** (055–076, 2026-09-29). Several of its
> entries have since moved on — ADR-036 is superseded by ADR-042, the player model is settled, the kangaroo
> and the Dry River overhaul are done. They are kept for the traps and the pipeline knowledge, not as a
> current task list.
>
> **The current order of work is `Docs/NEXT_PRIORITIES.md`** (updated 2026-10-01 from the producer's
> playtest verdict): character models and animations, weapon material/texture audit, VFX, weapon zeroing and recoil from
> real-world data, then the maps. Historical weapon measurements are explicitly labeled for revalidation. **§3.7 and §2's player-model row below are stale** — read
> `Docs/PLAYER_MODEL_PLAN.md` §5 and ADR-042 instead.

## 1. How the work is split

| Who | Where | Does |
|---|---|---|
| **Producer (Matt)** | Windows, `E:\SouthernSpear` | Decides, plays, screenshots, relays reports between agents |
| **Cloud Claude** (this role) | Linux container with a clone of the repo; **no Unreal, no Blender, no raw packs** | Design, ADRs, C++ and Python written blind, pure-logic checks (g++/Python), reviewing the other agents' reports, prompts for them |
| **Local agents** (Copilot/Codebuff/Claude on the producer's machine) | `E:\SouthernSpear` | Builds, automation tests, Blender and Unreal commandlets, in-game captures, LFS pushes |

The loop that works:
1. Cloud Claude writes the change, with checks it can run here.
2. It pushes to `main` and gives the producer a **paste-ready prompt** for a local agent: build, test, capture, report numbers.
3. The producer pastes back the agent's report and screenshots.
4. Cloud Claude reads the evidence critically and either fixes, redirects, or accepts.

Agents over-claim. Check their numbers against the code, and ask for measurements, not adjectives.

### Working rules from the cloud

- This is a historical handover, not current Git-operation guidance. In the shared checkout, inspect status and preserve other sessions' changes; do not commit or push unless explicitly requested.
- **Session numbers collide.** Before writing a changelog entry, `grep -n "^## Session" Docs/CHANGELOG.md | tail`, and take
  the next number. Risk IDs likewise: check the latest `R-` in the changelog **and** `Docs/PROJECT_AUDIT.md`.
- **Line endings:** `.gitattributes` is `eol=lf`, but some files are CRLF in the working tree. When editing with Python,
  detect `\r\n` and keep it.
- **What you can prove here:** `validate_architecture.py`, `check_unity_names.py`, `test_architecture_guard.py`, all
  `Tools/Common/test_*.py`, `Tools/Casualty/check_casualty_rules.py`, `Tools/Progression/rank_preview.py`. For new C++
  logic, **put the rules in an engine-free header and check it with g++ here** (see §3.2). It's the one way to prove C++
  from the cloud.
- **What you can't:** compile Unreal code, run the automation suite, see the game. Say so in the changelog's NOT RUN.

---

## 2. Where things stand (2026-09-29)

| Area | State | Next |
|---|---|---|
| Casualty care (ADR-040) | **Steps 1 and 2 built and passing:** 67/67 automation incl. `SouthernSpear.Casualty.*` (Session 078 run) | Step 3 investigation first (prompt C), then the bridge (§3.2) |
| Loading screens / front end | **Done in code, not built:** per-operation loading screen, one operation list, 3-column front end, "KILLS" label | Build, capture a load (§3.3) |
| Hand IK (W2) | **Historical status at 2026-09-29:** A88 accepted by the producer; Session 078 measured its wrist 4.54 cm from the bore using `GripNudgeCm`. Other weapon holds were unmeasured (R-85). The later hand-IK review confirms the hook changes the rendered pose; current R-65 remains broader fit/visual acceptance, not a hook-execution blocker. | Keep the historical per-weapon measurements distinct from the current acceptance status in `PROJECT_AUDIT.md` R-65/R-85 |
| Reload (W5) | Tooling exists; **Arma's AUG reload clips decode to impossible poses**; the magazine is welded into the mesh | An authored path, after R-86 (§3.5) |
| Casings / muzzle light (W3) | Code and tests pass (61/61 then 63/63 suites) | Muzzle flash: `NS_WeaponFire_MuzzleFlash_Rifle` (§3.6) |
| Player model / uniforms | **Superseded — see `Docs/NEXT_PRIORITIES.md` §2.** ADR-042 (2026-09-30): Quantum is the producer-selected friendly body with runtime retarget; final visual/camo capture remains pending | `PLAYER_MODEL_PLAN.md` §1 current state, then §5; §§2–4 are historical G3 diagnosis, not the active appearance |
| Grenade | A local agent was moving throw-grenade off **Q** (lean) to **G** and adding a model | Check it landed; ADFRC F1 grenade is available (§3.8) |
| Ravenshoe map | Built, dressed, lit; **nav not baked** (needs an attended editor bake, R-82) | Producer or local agent, attended |
| Unity-name check | **Fixed (Session 079):** the two "shadows" were false positives from the checker (assignments, not declarations); the checker now needs a type and a name. The cloud's earlier claim that this would break the Windows build was wrong | — |
| UI verification (Session 076) | **Verified by the local agent:** front end fits at 1080p (RULES row clear, cards 3+2); loading screens show the operation, rules and tip for Dry River (both rule sets) and Red Gum, with their own art. Captures are untracked on the producer's machine | Commit captures + `dryriver.png`/`redgum.png` + the two imported textures (LFS) |
| Callsign field | Written, uncompiled (Session 080): Settings > INTERFACE | Build; look at it in game |
| Casualty step 3 research | Done by the local agent: `Docs/evidence/casualty_lyra_hooks.md` (301 lines) — **untracked, not on GitHub** | Commit it; then the cloud designs the bridge from it |
| Assets | **Acquired project assets are producer-cleared for Southern Spear's F2P game** under ADR-028/035, reaffirmed 2026-10-01. Record available provenance/credits; seller flags do not create holds. No raw-source redistribution; commercial-game rips remain prohibited. | — |

---

## 3. Workstreams in detail

### 3.1 Decisions the producer has made this session (don't re-ask)

- ADR-040 casualty care **accepted**, with its build order. The medic's kit is a **treatment point, not a heal aura**
  (GDD §4.3: no passive regeneration).
- Producer direction clears acquired project assets for F2P use regardless of `isAiForbidden` metadata; this is project-specific, preserves credits/no-endorsement/content-ethics rules, does not authorize raw-source redistribution, and does not clear prohibited commercial-game rips (ADR-035, L-0016d).
- ADR-042 supersedes ADR-036 for the active friendly body: Quantum is selected. Do not reopen the G3-versus-Quantum selection without new producer direction; use a visual capture to validate the current appearance.
- Grenade on **G**, lean on Q/E.
- The LFS storage quota is a cost the producer is aware of. The repo must stay **private** (Lyra-derived copies are in it).

### 3.2 Casualty care — steps 2 to 4

Design: `Docs/DECISION_LOG.md` ADR-040. Rules: `Plugins/SouthernSpearCasualty/Source/SouthernSpearCasualty/Public/SSCasualtyRules.h`
(namespace `SSCasualty`, engine-free, std only). Checks: `Private/Tests/SSCasualtyRuleChecks.h`, run by both
`SouthernSpear.Casualty.Rules` and `python Tools/Casualty/check_casualty_rules.py`. **Add every new rule check there,
not in the UE test**, so it stays provable from the cloud.

**Step 2 (module side, no Lyra) — WRITTEN in Session 077, uncompiled.** The list below is what it was; kept as the spec to check the code against:
- `USSCasualtySettings` (`UDeveloperSettings`, config `Game`, section `/Script/SouthernSpearCasualty.SSCasualtySettings`):
  one `UPROPERTY(Config)` per `FTuning` field, and `ToTuning()`. Add `DeveloperSettings` to the Build.cs.
  **Warning (Session 074):** an ini array written in the wrong struct syntax "imports" as empty, silently. Read a
  distinctive value back in a test.
- `USSCasualtyComponent` (`UActorComponent` on the pawn, replicated):
  - Server-only mutators: `ApplyHit(EZone, RawDamage)`, `TickCasualty`, `BeginTreatment(Patient, Action)`,
    `CancelTreatment`, `CompleteTreatment`.
  - Replicated: state, bleed (quantised), bleed-out remaining, dressings, the treating instigator, treatment progress.
  - Make the rule enums `UENUM(BlueprintType)` mirrors in the component header, or static-cast them. Don't put `UENUM`s
    in the engine-free header.
- `ASSMedicalKit`: replicated actor holding an `FKit`. A mesh component that loads the IFAK mesh (path in settings, soft
  pointer). Charges replicated; destroys itself when `TickKit` returns false. One per medic (the server tracks the owner).
- **Where's the "no regeneration" guard?** Nothing in the component may raise health except `CompleteTreatment`. Add a UE
  test that ticks a component 120 s and asserts that.

**Step 3 (bridge, the only Lyra-touching part) — investigate before writing:**
- How to keep Lyra from killing the pawn at zero health while the casualty rules say Downed. Look at
  `ULyraHealthComponent` (`OnOutOfHealth`, `StartDeath`) and `ULyraHealthSet` (clamping in
  `PostGameplayEffectExecute` / `PreAttributeChange`).
  - Likely route: the bridge listens for damage, feeds the casualty component, and while Downed keeps Lyra's health above
    zero (or blocks the death ability) until the component says Dead. Then Lyra's normal death runs, and
    `USSRespawnGate::ReportElimination` fires **only** on Dead.
  - Ask a local agent to read the 5.8 Lyra source and report the exact hooks before you write it. Blind assumptions
    about Lyra/engine call paths have been wrong twice this session (R-65's "never runs", the FBX "transpose").
- Hit zone from the hit bone: map `head`/`neck_01` → Head, `spine_*`/`pelvis` → Torso, `*arm*`/`hand*` → Arm, `thigh*`/`calf*`/`foot*` → Leg.
  Put the table in settings.
- Interaction: hold-to-treat on the interact input; cancel on movement input or damage; a medic flag from the role
  (until roles exist, a settings flag `bEveryoneIsMedic` for testing).

**Step 4 (UI, `SouthernSpearUI`, through a Core state object like `USSLocalHudState`):** a bleed marker, the downed
bleed-out bar, "STABILISING…" progress, and kit charges when near a kit. Then **update the class-select Medic text**,
which currently says "Healing is not in the game yet."

### 3.3 UI

- Loading screen: `SSLoadingScreenWidget.cpp`; the destination comes from `USSMenuWidget::PendingMap()`, else the engine's
  travel URL.
- **Map art:** the producer supplies drone shots in `Docs/images/loadingscreens/` (`dryriver.png` is already there; any letter
  case matches, keys: RedGum, DryRiver, Saltbush, SelatCanal, Bluestone). Then `SS_UI_LOADING_ONLY=1` with `-ExecutePythonScript=.../setup_ui.py`.
  The same shots could later replace the front-end background per selected card (not done).
- **Operations list:** `Private/SSOperations.h` is the single list. Adding a map means adding it there **and** a handler in
  `SSMenuWidget` (the `ensure` catches a mismatch). Ravenshoe is not on the front end, deliberately, until its nav is baked.
- **Not done, worth doing:**
  - A **callsign field** on the front end. Today it's console only (`ss.Callsign`), so the scoreboard shows
    "hurleym-CB9A5F2A0CAF". UI can't depend on Progression (SS001), so it needs a request field or delegate on Core's
    `USSLocalProfileState` that Progression listens to.
  - The class-select preview holds an M4-pattern rifle while the card says A88.
  - **Motion blur** is Lyra's default and very strong. Turn it off or down in our post-process or settings.

### 3.4 Hand IK / weapon holds (historical implementation notes; current status in PROJECT_AUDIT R-65)

- The measured facts are in Sessions 067–078 of the changelog. Short version:
  - **Historical engine-trace finding:** `FinalizeBoneTransform` is reached via `PhysAnim.cpp:468`; Session 067–070's captures confirmed a rendered pose change and an A88 target measurement. Current R-65 remains fit/acceptance work, not hook execution.
  - The two-bone solve places the wrist.
  - `RotateChain` turns the hand to a frame built **at runtime** from the Muzzle and RightHandGrip sockets and the weapon's
    up.
  - The palm tilt comes from `GripPalmTiltDeg` in `DefaultGame.ini`, keyed by mesh name.
  - The arms' per-skeleton correction is `HandRotationOffset`.
- **A left hand's (palm, finger, thumb) triad is left-handed**: `palm = thumb × finger`. Getting this wrong gives a
  mirrored frame that still "matches" a mirrored target with 0.0° residual (Session 074). Any new hand maths needs a test
  asserting the handedness.
- **Historical R-86 prompt (superseded by Session 078):** the A88's grip socket sat 10.3 cm left of the bore. Session 078 added `GripNudgeCm=(Forward=-4.7,Right=5.4,Up=2.1)` and measured the wrist 4.54 cm from the bore with `wrist_to_target=0.00`; R-86 is closed for A88. Do not repeat the old proposed `(0,+5.5,-1.5)` values as current instructions. Other weapon hold positions remain unauthored/unmeasured under R-85.
- **Pistol arms (A9):** `SK_FP_Arms_Pistol` fills the lower screen with untextured tan forearms. Get the component scale,
  location and materials from a local agent first.
- **Right hand / bare hands** are flat tan with no glove material. That's a material job.

### 3.5 Reload (W5)

- `Tools/Common/adfrc_reload.py` turns a decoded clip into a left-hand path in the weapon's axes. It **refuses** any clip
  where the wrists end up more than 0.9 m apart.
- `GestureReloadAUG`/`…Prone` fail that check: the wrists come out 1.5–3.2 m apart, so Arma's gestures don't pose under
  our model (R-78). `MPP_Slow_Reload` passes but isn't the AUG.
- **Plan:** author the path from the weapon's own points: grip → `magazine_axis` memory point → a pouch point on the body
  → back to grip. Time it to Lyra's reload montage, with the magazine swap at 0.48.
- **The ADFRC magazine is welded into the gun mesh.** No named selections survived the conversion. A magazine that leaves
  in the hand needs a Blender split; for a first version, keep the magazine on the gun.

### 3.6 Effects

- Casings (`SSShellEjectSubsystem`) and the muzzle light (`SSMuzzleLightSubsystem`) are in, with `ss.Casings` and
  `ss.MuzzleLight` cvars.
- **Muzzle flash:** the Realistic Starter VFX pack has none. The candidates in the project are
  `NS_WeaponFire_MuzzleFlash_Rifle` (Lyra's own) and `P_AssaultRifle_MuzzleFlash` (the AK-47 pack), listed in
  `Docs/evidence/vfx_muzzle_candidates.json`.

### 3.7 Player model / uniforms — **SUPERSEDED, read `Docs/NEXT_PRIORITIES.md` §2**

The body question is closed by ADR-042: Quantum is the producer-selected friendly visual body on its own
skeleton, runtime-retargeted from the pawn mesh. The remaining task is visual validation, not a body-choice
comparison. Use `PLAYER_MODEL_PLAN.md` §1 for the current state; §§2–4 preserve the G3 findings as history
only. The 53% flat-fill finding belongs to the superseded G3 shirt and is not the active Quantum-body defect.

- Start with `Docs/PLAYER_MODEL_PLAN.md`. It's measured, not guessed, and gives the ordered plan.
- ADR-036–039 document historical G3/Quantum evaluation. ADR-042 is the current producer decision: Quantum friendly modules are selected; do not follow the old G3 comparison/selection instructions.
- The historical G3 uniform carries the arms and its sheet had a measured flat olive area (53%); this was a G3-specific finding. The active Quantum camo/fit appearance still needs a current in-game capture.
- R-58/R-59 are tracked audit rows, but their old G3-part counts and ownership description must not be applied to the current Quantum assembly without remeasurement.

### 3.8 Grenade

- Q was bound to both lean and throw-grenade. A local agent was moving the grenade to G, in our input config, not Lyra's.
- There's an **Australian F1 grenade** in the ADFRC pack (`Workshop/ADF_Weapons/adfrc_f1grenade`; its config didn't
  decode). Check `Art/ADFRC_BLEND/adfrc_f1grenade/` before modelling one.
- Change only the look: Lyra's ability, damage and explosion stay (ADR-004). The MAF grenade is a cosmetic variant (W-105).

---

## 4. Traps that cost time this session (read before touching the same areas)

1. **Quaternion conventions in ADFRC data:** the stored quaternions are read as (−x, −y, z, w). Decoder schema
   `adfrc-anim-local/2` writes standard quaternions; `/1` and unlabelled files use the stored convention. Mixing them
   double-flips silently. `adfrc_grip.to_stored_convention` handles it.
2. **Matrix layout:** `adfrc_grip` returns tuples of **rows** whose **columns** are axes; `mathutils.Matrix()` also
   takes rows. A stray `.transposed()` inverted the socket (Session 073). Blame your own code before the exporter.
3. **FBX export isn't reproducible:** `CreationTimeStamp` changes each rebuild, costing ~21 MB of new LFS per rebuild
   with no mesh change. Don't commit rebuilt FBX unless the mesh changed.
4. **GH008 on push:** new LFS objects need `git lfs push origin main` before `GIT_LFS_SKIP_PUSH=1 git push`. From the
   cloud this never arises.
5. **`-NoLoadingScreen`** is required for the automation suite. Without it, `TwoPlayerAuthoritySmoke` fails with
   `ViewportOverlayWidget` ensures (R-88). It's not a regression.
6. **Unity-build shadows** are compile errors on Windows (C4459). Run `check_unity_names.py` before pushing C++.
7. **Ini arrays of structs** can import as empty with only an `import failed` log line (Session 074). Verify with a
   distinctive value.
8. **Screenshots as evidence:** a single A/B pair is noisy (the camera and the world move between runs). Session 067
   used repeated runs, a per-tile noise floor, and checked which weapon was held.
9. **The decoder** (`Docs/Sourced/ADFRC/rtm_rigs.py`) now skips its own `Rig/` output, so it can be re-run.
10. **Engine behaviour claims:** verify in the 5.8 source via a local agent before building on them. Two confident
    claims this session were wrong.

---

## 5. Paste-ready prompts for local agents

**A. Build and verify what the cloud pushed (Sessions 075–077) — the full version, sent 2026-09-29:**
```text
Pull main (04fa827e or later). You are verifying code that was written WITHOUT a compiler or Unreal, so expect
small first-build errors (a missing include, a signature). Fix compile errors in the cloud's files minimally and
say exactly what you changed. Do not redesign anything. Do not touch animation, hand-IK or weapon files except
step 1 below, and only when the animation work is committed or you have asked the animation agent first.

Report format: for each step, the command, the exit code, the observed result, and the evidence path. Never write
PASS for something you did not execute.

1. python Tools/check_unity_names.py fails on SSHandIKProbeSubsystem.cpp (locals GHaveBodyFrame and
   GBodyFrameInWeapon shadow file-scope names; C4459 is an error on MSVC). Rename the locals. If someone is editing
   that file now, do this LAST and tell me. Expect exit 0 afterwards.
2. python Tools/validate_architecture.py and python Tools/Casualty/check_casualty_rules.py (needs g++ or clang on
   PATH; if there is none, say so and skip). Expect exit 0 and "53 checks, 0 failure(s)".
3. Build SouthernSpearEditor. New code to watch: Plugins/SouthernSpearCasualty (new plugin, enabled in the
   .uproject), SouthernSpearUI (SSOperations.h, SSLoadingScreenWidget, SSMenuWidget). Zero warnings expected;
   paste any.
4. Full automation suite WITH -NoLoadingScreen. Expect the previous total plus 4 tests:
   SouthernSpear.Casualty.Rules, .Settings, .Component, .Kit. Paste the Result= line for each of the four, and any
   failure's log lines. If Component or Kit fail, check the test fixture first (FBareWorld in
   SSCasualtyRuntimeTests.cpp builds a world by hand and ticks components manually), and report whether
   HasAuthority() was true before changing the rules.
   Settings: if it fails on the bone lists, the DefaultGame.ini [/Script/SouthernSpearCasualty.SSCasualtySettings]
   section did not import: report the "import failed" line.
5. Front end at 1920x1080: capture it (-SSShotAt or your usual method). The RULES row and its buttons must be fully
   visible above the disclaimer, and the five map cards must be three across (3 + 2).
6. Loading screens: run Tools/Unreal/setup_ui.py with SS_UI_LOADING_ONLY=1 (imports Docs/images/loadingscreens/
   dryriver.png as T_SS_Load_DryRiver; the other four keys report "no file yet"). Then deploy to Dry River from the
   front end once with OBJECTIVE ASSAULT and once with SECTION ASSAULT and capture the loading screen each time (a
   High Resolution Screenshot during the load, or hold the load open). Also deploy to Red Gum once (no art yet: it
   must show the key art with the map's text, not crash or go black). Check each screen shows: "LOADING OPERATION",
   the map name, its objectives/terrain line, its description, the rule set name and summary, and a tip. Report
   anything clipped, overlapping or unreadable.
7. Save captures under Docs/evidence/ui_session077/ and write a changelog session entry.

Git: only one agent writes git. Commit only your own paths with git commit --only -- <paths>. New LFS objects (the
imported texture is not in git, but captures are PNGs) need "git lfs push origin main" before
"GIT_LFS_SKIP_PUSH=1 git push". git fetch first: the cloud pushes to main too, and changelog conflicts are
resolved by keeping both entries in order.
```

**B. R-86, the left-hand position:**
```text
Add a per-weapon GripNudgeCm (forward, right, up in the hold frame) in Config/DefaultGame.ini next to GripPalmTiltDeg,
applied to the IK target in USSHandIKMeshComponent. Start with A88 = (0, +5.5, -1.5). Log the realised wrist-to-bore
distance (target 4-5 cm), and screenshot. Verify the ini value actually imports (read back a distinctive value, as in
Session 074). Add a test.
```

**C. Casualty step 3 investigation (before any bridge code):**
```text
Read the Lyra 5.8 source and report, with file:line: how ULyraHealthComponent decides death (OnOutOfHealth,
StartDeath, the death ability), where health is clamped in ULyraHealthSet, and how to keep a pawn alive at zero health
until our code says otherwise, without editing Lyra. Also report how damage events expose the hit bone (the
GameplayEffect context's hit result). Don't write code.
```

---

## 6. Open risks worth knowing (full list: `Docs/PROJECT_AUDIT.md`)

- R-09: no dedicated-server target on this engine install. Phase 1 criterion 1 is blocked until the engine is built
  from source.
- R-58/R-59: soldier skeleton and vertex budget.
- R-60: W1 reaches Lyra by reflection; source/config applies selected magazine/spare-ammo/spread/RPM rows, while `bFullAuto=false` enforcement remains incomplete.
- R-65: current hand-IK status is pose-change measured, with broader grip fit/acceptance open; do not follow Session 059's superseded "hook never runs" conclusion.
- R-78: ADFRC gesture clips don't pose.
- R-82: Ravenshoe nav needs an attended bake.
- R-84: the arms offset was solved against the old socket frame. Session 074 re-solved it against the runtime frame.
- R-85–R-88 (Session 074): hold tilt A88-only, grip socket position, hold fallback, the `-NoLoadingScreen` flag.
- R-89: casualty rules inert in play until the bridge wiring (step 3).
- **Audit hygiene:** `PROJECT_AUDIT.md` doesn't yet list R-78, R-84 or R-89. Add them the next time the audit is touched.
