# TEST PLAN — Southern Spear

**Document ID:** `Docs/TEST_PLAN.md`
**Status:** Baseline — Phase 0
**Last updated:** 2026-09-26

---

## 1. Principles

1. **No claim without evidence.** A test is only "passing" if a command was run and its output recorded. Invented results are a disqualifying failure.
2. **A listen server is not proof of dedicated-server networking.** Acceptance requires a packaged, separate server process.
3. **Both perspectives, always.** Anything touching team presentation is tested from each team's point of view, not just one.
4. **Server authority is asserted, not assumed.** Every damage, score and progression claim is tested from the server's side.
5. **Placeholders are tested for the system, not the art.** Tests never assert on final art quality.

---

## 2. Test Layers

| Layer | Tool | When it runs |
|---|---|---|
| **Unit** | UE Automation (`IMPLEMENT_SIMPLE_AUTOMATION_TEST`) | Every CI run |
| **Integration** | UE Automation + PIE | Every CI run |
| **Network (in-editor)** | PIE multi-client with `NetEmulation` | Every CI run |
| **Network (real)** | Packaged dedicated server + packaged clients | Nightly + release gate |
| **Manual** | Human play, both perspectives | Every feature merge |
| **Performance** | Unreal Insights, Network Profiler, `stat` | Weekly + release gate |
| **Security** | Automation + adversarial client | Nightly |
| **Leak** | Automation | Every CI run |

---

## 3. Naming Convention

```
SouthernSpear.Unit.<System>.<Case>
SouthernSpear.Integration.<System>.<Case>
SouthernSpear.Network.<System>.<Case>
SouthernSpear.Security.<System>.<Case>
SouthernSpear.Leak.<Surface>.<Case>
```

C++ macro pattern:

```cpp
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSPresentationDualPerspectiveTest,
    "SouthernSpear.Network.TeamPresentation.DualPerspective",
    EAutomationTestFlags::ApplicationContextMask | EAutomationTestFlags::ProductFilter)
```

---

## 4. Unit Tests

### 4.1 Progression

| ID | Test | Asserts |
|---|---|---|
| U-PROG-01 | Rank threshold at boundary | XP at exactly the threshold awards the rank |
| U-PROG-02 | Rank threshold below boundary | XP one below does not award |
| U-PROG-03 | Curve monotonicity | Account level never decreases as XP increases |
| U-PROG-04 | **No uncapped awards** | Every XP award rule has `MaxPerMatch` set |
| U-PROG-05 | No kill-ratio rewards | No award rule keys on kill/death ratio |
| U-PROG-06 | No idle awards | No award rule fires on time-in-round alone |
| U-PROG-07 | No AI farming awards | AI-sourced events capped separately |
| U-PROG-08 | Commendation award | Criteria met → awarded exactly once |
| U-PROG-09 | Data-driven check | Progression numbers absent from C++ (static scan) |

### 4.2 Qualifications & roles

| ID | Test | Asserts |
|---|---|---|
| U-QUAL-01 | Award unlocks dependents | Completing a module opens exactly its roles |
| U-QUAL-02 | **No over-unlock** | Completing a module opens no unrelated roles |
| U-QUAL-03 | Prerequisites enforced | Leadership locked until prerequisites met |
| U-QUAL-04 | Best result retained | Replaying with a worse score does not overwrite the best |
| U-QUAL-05 | **Qualification never revoked** | A completed qualification survives server unavailability |
| U-QUAL-06 | Role limits | Squad cap and team cap enforced |

### 4.3 Persistence

| ID | Test | Asserts |
|---|---|---|
| U-PERS-01 | Round-trip | Save → load → identical |
| U-PERS-02 | Schema versioning | `SchemaVersion` present and correct |
| U-PERS-03 | Migration chain | A v1 record migrates correctly to the current schema |
| U-PERS-04 | Forward-compat | An unknown future version is rejected safely, not mis-read |
| U-PERS-05 | Corrupt record | A malformed record is rejected without crashing |
| U-PERS-06 | **Local provider rejects claims** | `ValidateProgressionClaim` returns false on the dev provider |
| U-PERS-07 | Settings persistence | Settings survive a simulated restart |

### 4.4 Weapons & damage

| ID | Test | Asserts |
|---|---|---|
| U-WEP-01 | Magazine capacity | Ammo cannot exceed capacity |
| U-WEP-02 | Reload timings | Tactical and empty reloads differ and match data |
| U-WEP-03 | Fire mode availability | Weapon only offers its declared modes |
| U-WEP-04 | Chamber state | Empty-chamber weapons cannot chamber mid-magazine correctly |
| U-WEP-05 | Damage curve | Location falloff matches the data asset |
| U-WEP-06 | Recoil profile | Pattern matches the data asset within tolerance |
| U-WEP-07 | **Reference data not read by gameplay** | No gameplay function reads `Reference` (static scan) |
| U-WEP-08 | **Faction symmetry** | Gameplay data identical across factions — byte-comparable |
| U-DMG-01 | Incapacitation | Low torso damage incapacitates rather than kills |
| U-DMG-02 | Bleeding | Incapacitated actor bleeds at the configured rate |
| U-DMG-03 | Stabilisation | Stabilising stops bleeding |
| U-DMG-04 | **No in-round regeneration** | Health never increases during a round without treatment |
| U-DMG-05 | Self vs medic treatment | Self-treatment outcome is strictly worse |

### 4.5 Team presentation

| ID | Test | Asserts |
|---|---|---|
| U-PRES-01 | **Dual perspective** | Player A sees A=friendly, B=hostile; player B sees the inverse |
| U-PRES-02 | **Presentation is cosmetic** | The resolver's API exposes no gameplay type (static scan) |
| U-PRES-03 | **Hitbox invariance** | Presentation changes do not alter collision or hitboxes |
| U-PRES-04 | Symmetry | Same faction, same gameplay data |
| U-PRES-05 | Fallback on unset data | A missing presentation set fails visibly, not silently |

---

## 5. Network Tests (PIE)

### 5.1 Net emulation profiles

Applied via `NetEmulation` PIE configurations:

| Profile | RTT | Jitter | Packet loss | Purpose |
|---|---|---|---|---|
| `LAN` | 0 ms | 0 ms | 0% | Baseline |
| `Good` | 30 ms | 5 ms | 0% | Typical |
| `Typical` | 80 ms | 15 ms | 0.5% | Regional |
| `Poor` | 150 ms | 40 ms | 2% | Cross-region |
| `Bad` | 250 ms | 60 ms | 5% | Worst acceptable |
| `Lossy` | 100 ms | 20 ms | 10% | Degraded link |

**Acceptance:** at `Poor`, a player can complete an objective. At `Lossy`, the session remains playable without desync or disconnection. At `Bad`, the session does not corrupt state — failure is acceptable, corruption is not.

### 5.2 Test matrix

| ID | Test | Asserts |
|---|---|---|
| N-NET-01 | Team assignment replicates | Both clients see opposing teams |
| N-NET-02 | Team presentation, **both perspectives** | Correct faction each side, in the same match |
| N-NET-03 | Damage authority | Server applies damage; a forged client damage request is rejected |
| N-NET-04 | Weapon replication | Fire, reload, ammo and fire mode replicate correctly |
| N-NET-05 | Reload interruption | Cancelling a reload leaves correct state on both clients |
| N-NET-06 | Objective replication | Capture progress and state are consistent on all clients |
| N-NET-07 | Round lifecycle | Warm-up → live → end → restart, replicated |
| N-NET-08 | Scoreboard validity | Every row matches server state |
| N-NET-09 | Late join | A client joining mid-round sees consistent state |
| N-NET-10 | Disconnect/reconnect | A reconnecting player rejoins with a valid state |
| N-NET-11 | Map travel | Travel to a new layer preserves session and applies the new layer config |
| N-NET-12 | Faction identity under emulation | Presentation is correct at 150 ms / 2% loss |
| N-NET-13 | Ownership transfer | Weapon state transfers correctly on possession change |
| N-NET-14 | Dormancy | Significancy manager correctly de/re-activates actors |

### 5.3 PIE session matrix

| Session | Configuration | When |
|---|---|---|
| 2-client | 1 listen + 1 client, dedicated server | Every CI run |
| 2-client DS | Packaged DS + 2 packaged clients | Nightly |
| 4-client PIE | 4 clients, 2 per team, listen server | Every CI run |
| 4-client DS | Packaged DS + 4 packaged clients | Nightly + release gate |

> The 4-client DS session requires more than 32 GB RAM when the editor is also running (PROJECT_AUDIT R-05). Close the editor for this test, or distribute clients to a second machine.

---

## 6. Dedicated Server Validation

Explicitly **not** substitutable by a listen server.

| ID | Check | Command / method |
|---|---|---|
| DS-01 | Server target builds | `Build.bat SouthernSpearServer Win64 Development` |
| DS-02 | Server packages | `RunUAT.bat BuildCookRun -Target=SouthernSpearServer` |
| DS-03 | Client packages | `RunUAT.bat BuildCookRun -Target=SouthernSpear` |
| DS-04 | Client connects | Client joins by IP; connection confirmed in server log |
| DS-05 | Two clients, one server | Both join the same match |
| DS-06 | **Server has no client surface** | Server binary does not link rendering/UI modules |
| DS-07 | Authority holds | All damage/score/progression originates server-side |
| DS-08 | Server tick within budget | ≤ 8.0 ms at 30 Hz under load |
| DS-09 | Graceful shutdown | Server stops cleanly and logs the session summary |
| DS-10 | Headless operation | Runs with no GPU, no display |

---

## 7. Security Tests

| ID | Test | Asserts |
|---|---|---|
| S-01 | **Forged damage** | A client-submitted damage value is ignored; server recomputes |
| S-02 | Forged hit | A client cannot claim a hit the server did not detect |
| S-03 | Forged ammo | Client cannot refill ammunition client-side |
| S-04 | **Forged progression** | A client claiming qualification/XP is rejected |
| S-05 | Forged role | Requesting an unqualified role is denied |
| S-06 | Invalid requests | Malformed RPCs are dropped without crashing |
| S-07 | Rate limiting | Fire/chat/ping spam is throttled |
| S-08 | Name sanitisation | Injection attempts in names/chat are neutralised |
| S-09 | **No secrets in repo** | `git grep` for keys, tokens, endpoints with secrets |
| S-10 | Movement validation | Out-of-bounds movement (speed/teleport) is rejected |
| S-11 | Inventory validation | Client cannot grant itself equipment |
| S-12 | Admin audit | Every admin action is logged immutably |

---

## 8. Information Leakage Tests

Every surface where a player could receive information they should not have.

| Surface | Test | Asserts |
|---|---|---|
| **Spectator (own team)** | LEAK-01 | Sees only own team; no opposing detail |
| **Spectator (free-fly)** | LEAK-02 | Denied by default; elevated access is logged |
| **Spectator (post-death)** | LEAK-03 | No dead-outs; no enemy positions revealed |
| **Kill feed** | LEAK-04 | No information beyond the kill itself |
| **Scoreboard** | LEAK-05 | No opposing qualification or loadout detail |
| **Post-round summary** | LEAK-06 | No opposing intel a live player could not have had |
| **Replay** | LEAK-07 | Any replay respects the same restrictions |
| **Ping system** | LEAK-08 | Pings do not reveal the pinger's hidden position |
| **Voice indicators** | LEAK-09 | Channel activity does not leak through to the opposing team |
| **Reconnection** | LEAK-10 | Reconnecting reveals nothing about the interim |

---

## 9. Training Tests

| ID | Test | Asserts |
|---|---|---|
| TR-01 | Modules replayable | Any completed module can be replayed |
| TR-02 | Best result stored | Best score persists across replays and restarts |
| TR-03 | Qualification awarded | Passing awards exactly one qualification |
| TR-04 | Failure explained | Failure conditions are stated before and after an attempt |
| TR-05 | **Offline completion** | Training completes with no server available |
| TR-06 | **Survives downtime** | A completed qualification is not lost when a server is down |
| TR-07 | Accessibility options | Accessibility settings apply throughout training |
| TR-08 | Prerequisite chain | Leadership unreachable without prerequisites |

---

## 10. Performance Tests

| ID | Test | Budget | Tool |
|---|---|---|---|
| P-01 | Client frame time | 16.6 ms @1080p | Insights / `stat unit` |
| P-02 | Game thread | ≤ 8.0 ms | `stat game` |
| P-03 | Render thread | ≤ 10.0 ms | `stat rhi` |
| P-04 | Draw calls | ≤ 3,500 | `stat rhi` |
| P-05 | Server tick @30 Hz | ≤ 8.0 ms | `stat net` / Insights |
| P-06 | Bandwidth per client | ≤ 60 KB/s down | Network Profiler |
| P-07 | Server memory @64 | ≤ 12 GB | Task Manager / Insights |
| P-08 | Map travel (cold) | ≤ 25 s | Server log |
| P-09 | Texture memory | ≤ 1,200 MB | `stat texturegroup` |
| P-10 | Skeletal mesh cost | ≤ 6 ms GPU | `stat anim` |

**No performance claim without an attached trace.**

---

## 11. Manual Test Procedures

### 11.1 Dual-perspective verification (required for every presentation change)

1. Start a 2-client PIE session on a listen server, one player per team.
2. Client A: confirm own team renders as the friendly Australian force.
3. Client A: confirm the opposing team renders as the Murasian Armed Forces.
4. Client B: confirm own team renders as the friendly Australian force.
5. Client B: confirm the opposing team renders as the Murasian Armed Forces.
6. Confirm both clients see the **same** player as the same faction.
7. Repeat with colour-vision presets applied.
8. Repeat under `NetEmulation` profile `Poor`.

**Pass requires all eight steps.** Testing from one perspective is a failure.

### 11.2 Vertical slice acceptance run

Full scripted pass of all 14 criteria in `DEVELOPMENT_ROADMAP.md` §4.3, recorded with commands, logs and screenshots.

---

## 12. CI Integration

`.github/workflows/build.yml` executes on every push:

```
1. Assert MSVC version >= 14.44.34918
2. git lfs fsck
3. Static scan: presentation must not reference gameplay headers
4. Static scan: no progression numbers in C++
5. Static scan: no gameplay read of weapon Reference data
6. Static scan: no secrets
7. Static scan: every .uasset/.umap has a LICENCE_REGISTER entry
8. Build SouthernSpearEditor Win64 Development
9. Build SouthernSpearServer Win64 Development
10. Run Unit + Integration + Network + Leak automation tests
11. Upload results as a build artifact
```

Nightly additionally runs the packaged dedicated-server suite (§6) and load tests.

---

## 13. Test Execution Record

Every session appends to this table. **Empty means not tested — not passed.**

| Date | Suite | Command | Result | Evidence |
|---|---|---|---|---|
| 2026-09-26 | Toolchain audit | See `PROJECT_AUDIT.md` §9 | **PASS** | Terminal transcript in session log |
| 2026-09-26 | Git LFS configuration | `git check-attr filter diff merge text` | **PASS** | `.uasset`/`.blend` → `lfs`; `.md` → text |
| 2026-09-26 | Gate G0.8 Lyra compile | `Build.bat SouthernSpearEditor` | **PASS** | `CHANGELOG.md` G0.8 session |
| 2026-09-26 | Architecture guard (+ negative) | `python Tools/validate_architecture.py` | **PASS**; negative caught 4 | `Docs/evidence/G030_guard_*.txt` |
| 2026-09-26 | SouthernSpear.Core + .Presentation | `Automation RunTests SouthernSpear` | **PASS 15/15** | `Docs/evidence/G030_tests_keylines.txt` |
| 2026-09-26 | Dry River nav regression (R-11) | `-ExecutePythonScript=Tools\Unreal\build_dryriver_nav.py` | **PASS** (path 2 points; tiles not measured) | `Docs/evidence/R11_dryriver_nav_report.json` |
| 2026-09-26 | Dry River dressing data | `python Tools/verify_dressing.py` | **PASS 19/19** | `CHANGELOG.md` Session 006 |
| 2026-09-26 | Game Feature activation | `-game` on `/ShooterMaps/Maps/L_Expanse` | **PASS** (ShooterCore Active on demand) | `Docs/evidence/G031_gamefeature_activation_keylines.txt` |
| 2026-09-26 | SouthernSpear.Objectives (pure + world) | `Automation RunTests SouthernSpear` | **PASS**; suite 26/26 | `Docs/evidence/G040_tests_keylines.txt` |
| — | Two-player authority smoke | `Automation RunTests SouthernSpear.Network.Gameplay.TwoPlayerAuthoritySmoke` | **PASS** (2026-09-28, with `-NoLoadingScreen`) | `Docs/evidence/S035_tests.txt`; editor test worlds, not dedicated-server acceptance (R-09). |
| 2026-09-26 | Objective Assault live game | `-game` on `/Game/Maps/L_DryRiver_01` | **PASS**: experience loaded, round 1 InProgress | `Docs/evidence/G040_dryriver_objective_assault_game_keylines.txt` |
| — | Dedicated server | — | **NOT RUN** | R-09 |

---

## 14. Coverage Targets

| Area | Target |
|---|---|
| Progression / persistence maths | 100% of rules tested |
| Team presentation | 100% — every surface |
| Damage authority | 100% of entry points |
| Weapon data integrity | 100% of weapons |
| Objective replication | 100% of objectives |
| Security entry points | 100% |
| UI / menus | Manual, all screens, controller and mouse |
| Audio | Manual |
| Performance | Budget pass/fail only, not coverage-based |

---

## 15. Defect Policy

| Severity | Definition | Response |
|---|---|---|
| **S1 Critical** | Exploitable, crashes the server, or leaks information | Fix immediately; blocks release |
| **S2 Major** | Breaks a core loop or an acceptance criterion | Fix before the phase exits |
| **S3 Minor** | Degrades experience, has a workaround | Schedule |
| **S4 Cosmetic** | Visual or polish | Backlog |

A **known placeholder limitation is not a defect** as long as it is recorded in `ASSET_REGISTER.md`. A placeholder that behaves incorrectly **is** a defect.
