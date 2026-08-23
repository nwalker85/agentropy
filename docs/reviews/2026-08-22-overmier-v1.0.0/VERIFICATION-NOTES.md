# Verification notes — Overmier open technical review of Agentropy v1.0.0

**Status:** working notes, WIP. Not the author response.
**Reviewed artifact:** v1.0.0 — DOI `10.5281/zenodo.20818597` — `main@91df6c0` (identical to the reviewer's archive `nwalker85-agentropy-91df6c0`).
**Review received:** 2026-08-22, Kurt Overmier, *"Pressure-Testing Agentropy: From Conservation Metaphor to Accountable Agent Infrastructure"*, draft-for-author-review. Recommendation: **major revision**.
**Verification performed:** 2026-08-22, by the author's agent, against the local canonical checkout. Every code-level claim was checked against source; the headline claims were reproduced live with the scripts in this directory.
**Environments tested:** Python 3.14.7 / `cryptography` 46.0.4 (primary); Python 3.10.20 and 3.12.13 / `cryptography` 50.0.0 via `uv` (token-economy population demo only). Reviewer used Python 3.10.12 / `cryptography` 3.4.8.

Purpose of this file: (1) give the author a receipts pile for the response; (2) define the scope of **v1.0.1** (patch: fixes and wording corrections, no new architecture); (3) record what was *not* verified.

---

## 1. Claim-by-claim verification

Legend — **CONFIRMED**: reproduced or read directly in source. **OVERSTATED**: real finding, stronger wording than the code supports. **NUANCE**: accurate, but missing context worth stating.

### 1.1 Core mechanism

| # | Reviewer's claim | Verdict | Receipt | Paper text it contradicts |
|---|---|---|---|---|
| 1 | The conservation equation is an accounting identity; `L` is defined so it holds | **CONFIRMED** | `amt_core.py:420-421` — `signal = len(plaintext)`, `loss = layer.mass - signal`; assertion at `:448` | None — `paper/agentropy.md:590` already says "a tautology of symmetric encryption. It holds because subtraction works." Reviewer credits this. |
| 2 | `key_class` is plaintext metadata; environments read it to select a key | **CONFIRMED** | `amt_core.py:121` `key_class: str`; `amt_core.py:405` `env.derive_key_for_class(layer.key_class)` | `paper/cross_org_accountability.md:94` — an alpha environment "cannot even detect the existence of `beta` layers (they are indistinguishable from random bytes)" |
| 3 | `interact()` removes **every** matching layer per visit | **CONFIRMED** | `amt_core.py:404-432` loop; no count limit | `paper/token_economy.md §8.4` "costs exactly 3 layers"; `§8.5` "An agent with 12 beta layers has exactly 4 LLM calls" |
| 4 | "Consumption" is a Python list reassignment; ciphertext bytes remain copyable | **CONFIRMED** | `amt_core.py:435` `agent.layers = surviving_layers` | `paper/token_economy.md §8.2` "The encrypted form is gone. An agent cannot present the same layer twice" — **false as written** |

### 1.2 Token economy

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 5 | Gateway never compares layers removed to `base_cost` | **CONFIRMED** | `amt_token_economy.py:193-207` — `success` iff `layers_stripped > 0 and agent_survived`. `base_cost` appears only in `__repr__` (`:68`, `:242`) and the budget observer (`:290`). |
| 6 | 1-layer agent succeeds against a declared 3-layer price | **CONFIRMED — reproduced** | `verify_02_replay_with_ballast.py`: agent with 1 beta + alpha ballast → `outcome=success`. (Without ballast the agent dies, `outcome=died_paying` — `verify_01`. The demo's budget agent has ballast, so the reviewer's reading of the demo log is right.) |
| 7 | Demo prose contradicts demo log | **CONFIRMED** | `amt_token_economy_demo.py:209-211` prints "couldn't afford GPT-4 (needs 3 beta, had 1)" after the call log records `success`. |
| 8 | Copying an agent allows both copies to pay | **CONFIRMED — reproduced** | `verify_02`: `copy.deepcopy(agent)` → copy A `success`, copy B `success` against the same gateway. |
| 9 | 12 beta layers stripped in one visit (overcharge) | **CONFIRMED — reproduced** | `verify_02`: 12 → 0 beta layers, `outcome=success`. |

### 1.3 Cross-organizational accountability

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 10 | "Public ledger" is a mutable in-memory list; commitments unsigned, unanchored | **CONFIRMED** | `amt_extensions.py:304-314` `PublicLedger.commitments: list`; `publish()` is `append`. No signing or external anchoring anywhere in the module (grep `sign|anchor` → only timestamps from `time.time()`). |
| 11 | Honest-environment assumption collides with "without trust" | **CONFIRMED** (wording) | Paper states the assumption honestly at `paper/agentropy.md §11.1`. The collision is with the cross-org paper's *title* ("…Without Trust") and `§10.6` "No trust, no protocol, no consensus mechanism, no identity provider." |

### 1.4 Physical IoT

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 12 | Encode/decode round trip is not invertible | **CONFIRMED — reproduced to 3 decimals** | `verify_01`: 50 Wh → 45.396; 100 MB → 128.000; 500 ops → 453.960; 30 s → 26.984; 50 reads → 43.820. Causes: GCM overhead (28 B/layer) inflates decoded mass; `to_layer_specs` quantises to 256-B layers and caps payloads at 512 B (`amt_physical_iot.py:228-240`). |
| 13 | Scale demo builds a fresh topology per agent; no shared depletion | **CONFIRMED** | `amt_physical_iot_demo.py:404` `topo = build_route_topology()` inside the per-agent loop. |
| 14 | — (reviewer did not say this) | **NUANCE** | The battery-dependent mass gate *is implemented* (`amt_physical_iot.py:141-164`, recomputed at `:435`). The reported run never exercises it across agents. Correct phrasing: "implemented, not exercised in the reported experiment" — not "absent". |
| 15 | "Battery budget directly predicts survival distance" printed regardless of result | **CONFIRMED — reproduced** | `amt_physical_iot_demo.py:489` is unconditional. Live run: all four battery tiers → 0 survivors, avg 5.0 locations. |

### 1.5 Marketplace / ecology

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 16 | Regeneration clock starts at sim-time 0 while `last_tick` defaults to wall-clock, so elapsed clamps to zero and "passive regeneration does not occur during the simulation" | **OVERSTATED** | `amt_marketplace.py:64` `last_tick = field(default_factory=time.time)`; `:72-76` `elapsed = max(0, now - last_tick)` then `last_tick = now`. Only the **first** `tick()` loses its regeneration; it rebases `last_tick` to sim-time and every later tick regenerates normally. `verify_03` (through `MarketplaceTopology.tick`, pool `current=0`, rate 10/s, 0.5-s ticks): 0.0 → 5.0 → 10.0 → 15.0. With `max_steps=30` (`:355`) the simulation regenerates for 29 of 30 ticks. **It is a one-tick offset bug, not absent regeneration.** Factual correction to request. |
| 17 | Nutrient cycler counts the entire budget as cycled while accreting at most three layers | **CONFIRMED** | `amt_marketplace.py:172` `self._total_cycled += budget`; `:281` `for kc_name, payload in new_specs[:3]`. |
| 18 | No system-level equation connects removed mass to factory-created mass | **CONFIRMED** (by reading; the 300 B → 356 B figure not independently reproduced) | `NutrientCycler.cycle()` creates layers via `factory.create_layer`, each carrying fresh GCM overhead; nothing reconciles against what was deposited. |
| 19 | No reproduction; population can only stay level or decline; "carrying capacity" is a tail average; "speciation" is predefined profiles | **CONFIRMED** | `amt_marketplace_demo.py` constructs profiles; `:446-447` prints "Alpha-heavy agents thrive at feeding_a … Beta-heavy agents thrive at feeding_b" unconditionally. (Reviewer's 0/0 vs 2/1 survivor variance between runs not re-run here.) |

### 1.6 Ablation

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 20 | Random condition removes ~1 layer per env key rather than all matching | **CONFIRMED** | `amt_ablation.py:112-113` `n_to_remove = max(1, min(env.hazard_classes, len(agent.layers)))`. The in-code comment *intends* parity with control ("Match control's stripping rate: ~1 layer per env key class"); parity only holds when agents carry ≤1 layer per class. |
| 21 | Random condition invents a 50/50 signal/loss split | **CONFIRMED** | `amt_ablation.py:130-131` `signal = consumed // 2; loss = consumed - signal`. |
| 22 | Immortal condition returns zero signal by construction | **CONFIRMED** | `amt_ablation.py:66-75` hard-codes `total_signal=0`. |
| 23 | Stratification's 3:1 ratio is an input construction | **CONFIRMED** | `amt_ablation.py:279-300` rich = 4 data layers × 3 classes; poor = 4 data alpha + 4 empty beta + 4 empty gamma. |

### 1.7 Reproducibility

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 24 | Results vary across processes under different `PYTHONHASHSEED` | **CONFIRMED — reproduced, root-caused** | Token demo population (200 agents), seeds 0/1/2: successful calls 444 / 453 / 451; survivors 107 / 98 / 88; total tool calls 2,125 (paper: 2,113; reviewer: 2,090–2,206). **Root cause:** `amt_extensions.py:841` `Topology.reachable_from` iterates `self.edges[node_id]`, a `set` of `str` — neighbour order depends on the string hash seed, and `AgentBehavior.choose_node` breaks score ties by order. The `random` calls are all seeded; `os.urandom` payloads do not change lengths. One `sorted()` restores determinism. |
| 25 | Not a Python-version effect (author's check, not reviewer's) | **CONFIRMED** | Same demo under 3.10.20 → 448 / 104; 3.12.13 → 444 / 107; 3.14.7 → 444 / 107 (seed 0). |
| 26 | No test suite, dependency manifest, repeated-trial distributions, or CIs | **CONFIRMED** | Repo root: no `requirements*`, `pyproject*`, `tests/`. README says `pip install cryptography` unpinned. |

### 1.8 Interpretive claims about the paper

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 27 | The papers claim a "substrate-independent law of life" / "general theory of life-like dynamics" | **OVERSTATED** | `paper/agentropy.md:604` (Appendix C): *"This paper makes only the weaker, testable claim (a necessary condition for life-like dynamics); the stronger claim is argued in companion work."* Appendix C opens: *"none of this paper's empirical claims depend on them."* The deposited paper's claim is the necessary-condition claim in `§7.4` and `§13`. The review's "smaller than a substrate-independent law of life" attributes a deferred claim to v1.0.0. Ask that the hedge be preserved. |
| 28 | The paper claims cryptographic scarcity / no double-spending | **CONFIRMED** | `paper/agentropy.md:250` "Conservation eliminates inflation, double-spending, and unauthorized access because mass is physical"; `paper/token_economy.md §8.2`. These sentences are wrong as written and need rewriting, not defending. |

**Score:** 26 of 28 checked items confirmed; 2 overstated (#16, #27); 1 nuance to add (#14).

---

## 2. Findings beyond the review

1. **Nondeterminism root cause** (item 24): `set` iteration in `Topology.reachable_from`, `amt_extensions.py:841`. Also `amt_core.py:267` returns `set(self.secrets.keys())` for hazard classes — harmless today (only used for counts/membership) but worth sorting for the same reason.
2. **`ResourcePool.regenerate(current_time)` uses `current_time or time.time()`** (`amt_marketplace.py:72`): a sim-time of exactly `0.0` silently falls back to wall-clock. Latent; fix alongside item 16.
3. **The "immortal" ablation condition is the copy-attack regime.** The proper control for "depletion" is *decrypt without destroy* — extract signal, keep the layer. That is exactly what a cloned agent gets (item 8). Reframed this way, the reviewer's double-spend finding and the ablation are the same experiment: without enforced destruction, signal is unbounded and the stratification/selectivity results dissolve. This is a v2 design point, not a v1.0.1 fix, but it is the honest way to state what the ablation *does* show.

---

## 3. Scope for v1.0.1 (patch)

Semantic-versioning patch: **fixes and corrections only.** No uniqueness, settlement, signing, or external anchoring — those change the threat model and belong to v2 with their own design record. A new Zenodo version deposit will mint a version DOI under the existing concept DOI; the v1.0.0 DOI stays immutable and the review keeps pointing at it.

### 3.1 Code fixes

| Priority | Fix | Files | Closes item(s) | Reviewer rec. |
|---|---|---|---|---|
| P0 | Determinism: `sorted()` neighbour iteration; sort hazard-class sets | `amt_extensions.py:841`, `amt_core.py:267` | 24 | #8, #10 |
| P0 | Gateway price enforcement: select exactly `base_cost` layers of the tool class; reject underfunded payment *before* tool execution; outcome `insufficient_funds` | `amt_token_economy.py:165-215`; needs a bounded-count variant of `interact()` in `amt_core.py` | 3, 5, 6, 7, 9 | #4 |
| P1 | Marketplace regeneration clock: initialise `last_tick` from sim-time (pass `sim_time` at construction, or set on `add_node`); remove the `or` fallback | `amt_marketplace.py:64, 72` | 16, §2.2 | — |
| P1 | Nutrient accounting: `_total_cycled` counts only what was actually accreted; return unused budget to the pool or record it as loss | `amt_marketplace.py:172, 281` | 17 | #7 (partial) |
| P1 | Remove unconditional "KEY INSIGHT" prints, or compute them from the measured result (survival-distance, "thrive", "could not afford") | `amt_physical_iot_demo.py:489`, `amt_marketplace_demo.py:446-447`, `amt_token_economy_demo.py:209-211` | 7, 15, 19 | #9 |
| P1 | IoT scale demo: one shared topology across agents so the mass gate is actually exercised; report decoded-vs-requested budget error in the demo output | `amt_physical_iot_demo.py:404` | 12, 13, 14 | — |
| P2 | Ablation controls: random condition removes the *same count* the control would; derive signal/loss from actual decryption of the removed layers instead of `// 2`; stratification poor-agents hold equal *total* data mass redistributed, not padding | `amt_ablation.py:112-131, 279-300` | 20–23 | #8 |
| P2 | `requirements.txt` / `pyproject.toml` pinning `cryptography`; `tests/` turning the headline assertions into pytest (conservation identity, price enforcement, determinism across `PYTHONHASHSEED`, regeneration after N ticks, copy-replay **documented as a known limitation test**, not a pass) | repo root | 26 | #10 |
| P2 | Multi-seed runner: N seeds → mean ± CI for calls/survivors; replace single-run numbers in the papers' tables | `amt_scale.py` or new `amt_trials.py` | 24, 26 | #8 |

### 3.2 Paper wording corrections (same release)

| File:line | Current | Problem | Direction |
|---|---|---|---|
| `paper/token_economy.md §8.2` | "The encrypted form is gone. An agent cannot present the same layer twice" | False — item 8 | State: destruction is local to the holder's process; uniqueness across copies requires an authority outside the scheme (v2). |
| `paper/agentropy.md:250` | "eliminates inflation, double-spending, and unauthorized access because mass is physical" | False — items 8, 28 | Narrow to what holds: no mass creation outside the factory; depletion is irreversible *within an honest process*. |
| `paper/cross_org_accountability.md:94` | "cannot even detect the existence of beta layers" | False — item 2 | Either encrypt the class tag (v2) or restate: class *presence* is visible, class *content* is not. |
| `paper/cross_org_accountability.md` title + `§10.6` | "Without Trust"; "No trust, no protocol…" | Collides with `§11.1` — item 11 | "Without a trusted intermediary *for the arithmetic*" — each org verifies its own consumption; cross-party non-repudiation is out of scope. |
| `paper/token_economy.md §8.4–8.5` | "costs exactly 3 layers"; "exactly 4 LLM calls" | False until P0 price enforcement lands — items 3, 5 | Becomes true after the fix; keep, but cite the enforcing code. |
| `paper/physical_iot.md:135` | "from previous agents consuming it" | Not exercised — item 13 | Becomes true after the shared-topology fix; otherwise delete. |
| `paper/agentropy.md §8.1` table; `§4.4`, `§6.4` | Single-run integers (2,113; 91; 2,095…) | Item 24 | Replace with multi-seed mean ± CI once the runner exists. |
| `paper/agentropy.md §9` | "establishes necessity" | Items 20–23 | After control repair: "consistent with"; keep "necessary condition" as the hypothesis, not the result, unless the repaired ablation supports it. |
| `paper/agentropy.md §6`, `marketplace.md` | "carrying capacity", "speciation", "boom/bust" | Item 19 | Use "tail-average population", "niche-differential survival", "monotonic decline" until reproduction exists. |

### 3.3 Explicitly out of scope for v1.0.1

- Uniqueness / anti-replay (signed capabilities, settlement) — reviewer recs #3, #6. Threat-model change → v2 + design record.
- Hiding key classes cryptographically — rec #5. v2.
- Global mass equation across factory/accretion/pools — rec #7. v2 (can be *measured* and reported in v1.0.1 without being *enforced*).
- Reproduction in the ecology model — `§12.1` future work. v2.
- Renaming the central result — rec #1. Author's call; wording, not code.

---

## 4. Inputs for the author response (facts only; prose is the author's)

**Concede outright (all verified):** items 2, 3, 4, 5–9, 10, 12, 13, 15, 17, 18, 19, 20–24, 26, 28. Accept "major revision".

**Request factual correction:**
- Item 16 — regeneration is a one-tick offset, not absent; 29 of 30 ticks regenerate. Receipt: `verify_03_regen_topology.py`.
- Item 27 — v1.0.0 explicitly makes only the necessary-condition claim and defers the definition-of-life claim to companion work (`paper/agentropy.md` Appendix C). Preserve the hedge.

**Add nuance:** item 14 — the battery gate mechanism exists; the reported run doesn't exercise it.

**Offer as author's own finding:** the `set`-iteration root cause (item 24) and the Python-version check (item 25) — the reviewer reported the symptom; the cause is now known and the fix is one line.

**Post-v1 work, to be attributed separately (per the reviewer's request):** the reviewer's closing stack — *signed authority → unique capability → typed budget → atomic settlement → local receipt → independent witness* — maps onto work completed after the deposit: a witness/judge separation for receipts, an authority/PDP, signed expiring capabilities, and the enacted-capacity vs attested-knowledge distinction for custody. None of it is in v1.0.0 and none of it rescues v1.0.0's claims; it is where recs #2, #3, #6 are being answered.

---

## 5. Not yet verified / open

- Reviewer's attachments (evidence matrix; `2026-08-21-agentropy-targeted-verification.py`) not yet obtained — obtain and run against `main@91df6c0`.
- Nutrient test figures (300 B → 356 B two-class; 440 B five-class) not independently reproduced.
- Marketplace speciation run-to-run variance (0/0 vs 2/1 survivors) not re-run.
- 50,000-agent scale run not re-run here (reviewer: 280.77 s, 2,286,167 interactions, 0 assertion failures).
- `paper/marketplace.md` and `paper/physical_iot.md` not read end-to-end for additional wording that the fixes above would invalidate.

## 6. Reproduction commands

```bash
# from the worktree root
python3 docs/reviews/2026-08-22-overmier-v1.0.0/verify_01_replay_regen_iot.py
python3 docs/reviews/2026-08-22-overmier-v1.0.0/verify_02_replay_with_ballast.py
python3 docs/reviews/2026-08-22-overmier-v1.0.0/verify_03_regen_topology.py
for s in 0 1 2; do PYTHONHASHSEED=$s python3 amt_token_economy_demo.py | grep -E 'Total tool calls|Successful calls:    |Agents surviving'; done
uv run --python 3.10 --with cryptography python amt_token_economy_demo.py | grep -E 'Successful calls:    |Agents surviving'
```
