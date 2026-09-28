# Locomotion and Animation Audit

**Date:** 2026-09-27 (Session 030). **Status:** Audit and roadmap for producer approval. **No movement or
animation change has been made against this document yet.**

**Brief (producer):** rebuild locomotion and animation to a tactical standard. The target feel is 40%
Ground Branch, 30% America's Army 2, 20% Squad and 10% Ready or Not. Use Lyra and Epic's Game Animation
Sample as reference architectures. Audit first, then change things in staged, tested commits.

Every finding in §2 comes from executed evidence in this session (named in brackets), not from memory.

---

## 1. The current movement stack, layer by layer

| Layer | What runs today | Owner |
|---|---|---|
| Input | Lyra Enhanced Input (`IMC_Default`: move, look, jump, crouch, fire, ADS, reload) | Lyra (vendored) |
| Movement | `ULyraCharacterMovementComponent` on `B_Hero_ShooterMannequin` | Lyra |
| Body animation | `ABP_Mannequin_Base` plus linked item layers (`ABP_RifleAnimLayers`, `ABP_PistolAnimLayers`, …, base `ABP_ItemAnimLayersBase`) | Lyra |
| Visible body | Fab soldier meshes (3 ACR: Quantum military character; MAF: conventional parts) that copy Lyra's invisible mannequin's pose bone for bone (`ASSCharacterPartActor`, leader pose) | Southern Spear (Team) |
| Held weapon, third person | Lyra `B_Rifle` / `B_Pistol` children with the Lyra mesh hidden and our ADFRC static mesh (`SSVisual`) added | Southern Spear (`setup_weapons.py`) |
| First person | Camera at the head bone; a **camera-held** copy of the weapon (`USSFirstPersonSubsystem`) with coded bob, sway, recoil kick and reload dip; own body hidden; no arms | Southern Spear (bridge) |
| Camera | `USSFirstPersonCameraMode` / ADS mode (FOV from settings) | Southern Spear (bridge) |

### 1.1 Movement values in use [editor script `audit.py`, `B_Hero_ShooterMannequin` defaults]

| Property | Value | Tactical-shooter reading |
|---|---:|---|
| Max walk speed (Lyra's only ground speed: a jog) | 600 cm/s (6.0 m/s) | Fast. There is no walk, sprint or tactical pace. |
| Crouched speed | 300 cm/s | Fast for a crouch. |
| Max acceleration | 1200 cm/s² | Reaches full speed in 0.5 s: arcade. |
| Walking braking deceleration | 1400 cm/s², friction 8, separate braking | Near-instant stops, no momentum. |
| Rotation | Controller yaw (always strafing), 720°/s | Correct for an FPS. |
| Jump Z velocity / air control | 500 / 0.4 | High air control: arcade. |
| Max step height / walkable floor angle | 50 cm / 44.8° | Fine. |

### 1.2 Animation techniques already in Lyra's graphs [node names found in the uassets]

| Requested | In Lyra today | Where |
|---|---|---|
| Distance matching | **Yes** (starts, stops; `PredictGroundMovementStopLocation`) | `ABP_ItemAnimLayersBase` |
| Stride warping | **Yes** | item layers |
| Orientation warping | **Yes** | item layers |
| Turn in place | **Yes** (root yaw offset) | base ABP and item layers |
| Foot IK / placement | **Yes** (FootPlacement, LegIK) | base ABP and item layers |
| Aim offsets | **Yes** | item layers |
| Upper-body weapon overlay | **Yes** (layered bone blends per weapon type) | item layers |
| Hand IK | **Yes** | item layers |
| Pivots, jump start / apex / land | **Yes** | base ABP |
| Motion matching | **No** (no Pose Search databases; PoseSearch, Chooser and MotionWarping plugins not enabled) | — |
| Motion warping (vault, mantle) | **No** | — |
| Lean, prone, sprint, vault, mantle, ladder, ready stances | **No** | — |

**Conclusion.** The body animation underneath our soldiers is modern (Lyra 5.x). The "amateur,
disconnected" feel comes from the layers Southern Spear put on top, and from the movement tuning (§2).

---

## 2. Findings

| # | Finding | Evidence | Severity |
|---|---|---|---|
| F1 | **First-person weapon floats.** It is attached to the camera, not to hands, and its motion is coded rather than driven by the body. By construction it cannot look physically connected. | `SSFirstPersonSubsystem.cpp`; producer: "animations are still terrible" | Critical |
| F2 | ~~Third-person weapons are rotated about 90°.~~ **Withdrawn after measurement.** Lyra's own rifle, drawn over ours (`ss.Debug.ShowLyraWeapon`), overlaps our mesh exactly; the socket data agrees (Lyra's rifle points along +Y from its grip, and ours maps onto that axis). The "rifle pointing up" was **Lyra's jog pose**, which carries the rifle high across the chest: see F5. The left hand does not reach the handguards of our longer or bullpup weapons, because Lyra's hand IK is tuned to its own rifle. | Bot-follow captures with both meshes drawn; socket log (`-SSAnimDebug`) | High (as F5 plus hand IK) |
| F3 | **Visible bodies are not the animated skeleton.** Fab meshes copy Lyra's invisible mannequin bone for bone. Their proportions differ (hand, shoulder and head positions), so Lyra's hand IK and aim offsets are tuned for a different body. | `ASSCharacterPartActor` (leader pose), ADR-022 | High |
| F4 | **Movement tuning is arcade:** 6 m/s jog, 0.5 s to full speed, near-instant stops, high air control. | §1.1 | High |
| F5 | **Lyra's animation set is stylised hero animation** (bouncy, exaggerated), not a tactical one. | Lyra content; producer target games | High |
| F6 | **Missing tactical states:** walk toggle, sprint, prone, lean, vault, mantle, ladder, low and high ready. | §1.2 | High |
| F7 | **Two dead first-person paths:** the Fab arms pack (`ss.FP.Arms`, AKS74U poses) and true first person (`ss.FP.BodyView`) are both switched off. | `SSFirstPersonSubsystem.cpp` | Low (cleanup) |
| F8 | Tick use in presentation: the first-person subsystem walks the pawn's attached actors every frame; the minimap runs its own scene capture. | Source review | Low |
| F9 | Replication: the view model and camera are local-only (correct). Any new movement state (sprint, lean, prone) must be replicated through the movement component with saved moves, not a Blueprint variable. | Design | Must-do |

---

## 3. Target architecture

The approach: keep what Lyra does well (layered, data-driven, replicated), take full-body motion matching
from the Game Animation Sample, and put the first person on the real body.

```
Enhanced Input ─► ASSCharacter (C++, child of ALyraCharacter)
                    └─ USSCharacterMovementComponent (C++)
                         stances (stand / crouch / prone), gaits (walk / tactical / jog / sprint),
                         lean; replicated with saved moves; tactical acceleration and braking
                  ─► ABP_SS_Soldier (our anim blueprint, on OUR skeleton-compatible body)
                         Full body:   Motion Matching (Pose Search databases per stance and gait)
                                      + Chooser tables for traversal
                         Warping:     orientation, stride, distance matching (from MM trajectory)
                         Feet:        foot placement, slope adaptation
                         Upper body:  weapon overlay layers (Lyra item layers adapted) + aim offset
                                      + additive ready poses (low / combat / high) + lean additive
                         Hands:       left-hand IK to the weapon's grip socket (every weapon)
                  ─► First person = the same body (Ground Branch model)
                         camera on the head socket; arms and weapon are the real third-person rig;
                         procedural layer on top: sway, inertia, breathing, recoil, stance transitions
```

**Decisions this needs (producer):**

1. **Add the Game Animation Sample (GASP)**, free from Epic, to supply the motion-matching databases and
   traversal animations. It needs a manual "Add to project" from Fab (§5). Epic content stays git-ignored
   (R-14).
2. **Enable engine plugins:** Pose Search (motion matching), Chooser and Motion Warping.
3. **A new C++ character and movement component** (`ASSCharacter`, `USSCharacterMovementComponent`)
   in the Lyra bridge. Lyra stays unmodified. This is an architecture change: it needs **ADR-024**.
4. **One skeleton for the visible body.** Either retarget the Fab soldier meshes to the UE5 mannequin
   skeleton (they share bone names, so only proportions differ), or skin our gear to Manny, as ADR-020
   planned originally.

---

## 4. Roadmap (staged; each stage is a commit with tests and evidence)

| Stage | Work | Needs new assets | Proves |
|---|---|---|---|
| **S0** | Left-hand grip socket on every weapon, as the hand IK target for S2 and S4 (F2 withdrawn: the attachment is correct) | No | Socket report; bot-follow capture |
| **S1** | ADR-024; `ASSCharacter` + `USSCharacterMovementComponent` (C++): tactical speeds (walk 1.6, tactical 2.4, jog 3.6, sprint 5.2 m/s), lower acceleration and braking for momentum, low air control; replicated gait and stance with saved moves; Enhanced Input actions (walk toggle, sprint, lean, prone) in our own mapping context | No | Automation tests on the speed and stance rules; two-player replication test |
| **S2** | True first person on the body: camera on the head socket, a high-ready first-person pose and aim offset, left-hand IK, procedural layer (sway, inertia, breathing, recoil, stance transitions); remove the camera-held view model and the arms-pack code (F7) | No (Lyra poses for now) | Captures at hip, ADS, sprint, crouch; weapon always in both hands |
| **S3** | Motion matching: `ABP_SS_Soldier` from GASP's reference graph; Pose Search databases per gait and stance; orientation / stride warping and foot placement from GASP | **GASP** | Captures and a recorded run cycle; stop and start distance check |
| **S4** | Weapon overlays: Lyra item layers adapted to the GASP body; low / combat / high ready additives; lean additive | Ready-pose animations (§5) | Captures per ready state |
| **S5** | Crouch and prone, traversal (vault and mantle with Motion Warping), landing, ladder | GASP traversal; prone and ladder sets (§5) | Traversal test course map |
| **S6** | Cleanup: remove dead first-person code and unused content references, reduce tick (event-driven attached-actor scan), document the graphs with state diagrams | No | Guard, tests, profile capture |

S0–S2 need nothing new and fix the critical finding F1. S3 onward need GASP.

---

## 5. Required animations and missing assets

| Set | Needed for | Available now | Source if missing |
|---|---|---|---|
| Idle / walk / jog / sprint cycles, starts, stops, pivots (8 directions) | Motion matching | Lyra (stylised) | **GASP** |
| Turn in place (stand, crouch) | Turn in place | Lyra | GASP |
| Crouch locomotion | Crouch walk | Lyra | GASP |
| Jump, fall, land (light / heavy) | Jump, landing | Lyra | GASP |
| Vault, mantle (low / high), hurdle | Traversal | none | **GASP traversal** |
| Prone idle, crawl, crouch↔prone transitions | Prone | none | **Missing**: Fab / marketplace military locomotion pack, or motion capture |
| Lean left / right (stand, crouch) | Lean | none | Procedural additive (spine chain) at first; authored poses later |
| Ladder climb (enter, loop, exit) | Ladder | none | **Missing**: pack or authored |
| Rifle and pistol upper-body overlays; low, combat and high ready; reloads per weapon | Weapon overlays | Lyra (rifle, pistol, shotgun) | Lyra, then weapon-specific sets |
| First-person arms and gloves (skinned to Manny) | S2 hands | none on our body | ADR-020 gear, or retargeted Fab gloves (downloaded, not added) |

**Missing and needing a producer action:**
1. Game Animation Sample: Fab / Epic, free; "Add to project".
2. A prone and ladder animation set.
3. The downloaded gloves pack: "Add to project".

---

## 6. Explicit non-goals

No sliding, no hero movement, no fast acceleration, no bunny hopping or air strafing (brief: "avoid").
Presentation stays local and never changes gameplay (ADR-004). Movement changes are gameplay: they live in
the new movement component, replicated, and are covered by tests.

## 7. Requested decisions (summary)

1. Approve the target architecture (§3) and ADR-024 (a C++ character and movement component in the bridge).
2. Approve enabling the Pose Search, Chooser and Motion Warping plugins.
3. Add the Game Animation Sample (and, if available, prone, ladder and gloves packs) to the project.
4. Choose the visible-body direction: retarget the Fab soldiers, or build our own gear on Manny.
5. Confirm starting with S0–S2, which need no new assets.
