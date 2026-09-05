# Verification notes — Overmier open technical review of Agentropy v1.0.0

**Status:** working notes. Round 1 (2026-08-22) + round 2 (2026-09-04/05). Not the author response.
**Reviewed artifact:** v1.0.0 — DOI `10.5281/zenodo.20818597` — `main@91df6c0` — tag `v1.0.0`. Identity proven in §0 (round 2).
**Review received:** 2026-08-22, Kurt Overmier, *"Pressure-Testing Agentropy: From Conservation Metaphor to Accountable Agent Infrastructure"*, draft-for-author-review. Recommendation: **major revision**. Package: review draft (11 sections), evidence matrix (23 rows), `2026-08-21-agentropy-targeted-verification.py`.
**Verification performed:** round 1 2026-08-22 against the local canonical checkout; round 2 2026-09-04/05 against the **bytes downloaded from Zenodo** (not the checkout), plus the reviewer's own harness and evidence matrix. Every code-level claim was checked against source; every headline number was reproduced live with the scripts in this directory or the reviewer's harness.
**Environments tested:**
- Round 1: Python 3.14.7 / `cryptography` 46.0.4 (primary); Python 3.10.20 and 3.12.13 / `cryptography` 50.0.0 via `uv` (token-economy population demo only).
- Round 2: Python 3.14.7 / `cryptography` 46.0.4 (all demos, all scripts, scale run); Python 3.10.20 / `cryptography` 50.0.1 and **Python 3.10.20 / `cryptography` 3.4.8 — the reviewer's exact library version** (reviewer's harness only).
- Reviewer: Python 3.10.12 / `cryptography` 3.4.8.

Purpose of this file: (1) give the author a receipts pile for the response; (2) define the scope of **v1.0.1** (patch: fixes and wording corrections, no new architecture); (3) record what was *not* verified.

---

## 0. Artifact identity (round 2)

Kurt reviewed only the public deposit. Round 2 analysed the same bytes.

| Check | Result |
|---|---|
| Zenodo record `20818597` file | `nwalker85/agentropy-v1.0.0.zip`, 146,189 B, record metadata `md5:6a2315a50bbb2d49dd1db9aa8e195785` |
| Downloaded zip md5 | `6a2315a50bbb2d49dd1db9aa8e195785` — matches record metadata and the reviewer's evidence-matrix row 2 |
| Zip top-level directory | `nwalker85-agentropy-91df6c0` — matches the reviewer's stated snapshot |
| `git rev-parse v1.0.0^{commit}` | `91df6c05e275fb8d3cb638f22b8db4092564898e` |
| `git rev-parse main` / `origin/main` / `origin refs/tags/v1.0.0` | all `91df6c05e275fb8d3cb638f22b8db4092564898e` |
| File-by-file sha256, zip vs `git archive v1.0.0` | 25 files each; **all 25 identical** (`diff` empty) |

Script: `identity_proof.sh` (in this directory). The extracted Zenodo tree is what every round-2 run below executed against.

---

## 1. Claim-by-claim verification

Legend — **CONFIRMED**: reproduced or read directly in source. **OVERSTATED**: real finding, stronger wording than the code supports. **NUANCE**: accurate, but missing context worth stating. **NOT-REPRODUCED**: attempted here and did not reproduce, or could not be attempted (reason stated).

### 1.1 Core mechanism

| # | Reviewer's claim | Verdict | Receipt | Paper text it contradicts |
|---|---|---|---|---|
| 1 | The conservation equation is an accounting identity; `L` is defined so it holds | **CONFIRMED** | `amt_core.py:420-421` — `signal = len(plaintext)`, `loss = layer.mass - signal`; assertion at `:448` | None — `paper/agentropy.md:590` already says "a tautology of symmetric encryption. It holds because subtraction works." Reviewer credits this. |
| 2 | `key_class` is plaintext metadata; environments read it to select a key | **CONFIRMED** | `amt_core.py:121` `key_class: str`; `amt_core.py:405` `env.derive_key_for_class(layer.key_class)` | `paper/cross_org_accountability.md:94` — an alpha environment "cannot even detect the existence of `beta` layers (they are indistinguishable from random bytes)"; `:97` "The environment cannot determine that beta and gamma layers exist." |
| 3 | `interact()` removes **every** matching layer per visit | **CONFIRMED** | `amt_core.py:404-432` loop; no count limit | `paper/token_economy.md:297` "costs exactly 3 layers"; `:303` "An agent with 12 beta layers has exactly 4 LLM calls"; `:103` "an agent with 3 beta layers can make exactly 1 LLM inference call" |
| 4 | "Consumption" is a Python list reassignment; ciphertext bytes remain copyable | **CONFIRMED** | `amt_core.py:435` `agent.layers = surviving_layers` | `paper/token_economy.md:282` "The encrypted form is gone. An agent cannot present the same layer twice" — **false as written** |

### 1.2 Token economy

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 5 | Gateway never compares layers removed to `base_cost` | **CONFIRMED** | `amt_token_economy.py:195-207` — `success` iff `layers_stripped > 0 and agent_survived`. `base_cost` appears only in `__repr__` (`:68`, `:242`) and the budget observer (`:290`). |
| 6 | 1-layer agent succeeds against a declared 3-layer price | **CONFIRMED — reproduced ×4** | `verify_02_replay_with_ballast.py`: agent with 1 beta + alpha ballast → `outcome=success`. Reviewer's harness (§1.9): `copied_state_calls[*].success = true, layers_charged = 1` vs `declared_llm_cost = 3`. (Without ballast the agent dies, `outcome=died_paying` — `verify_01`. The demo's budget agent has ballast, so the reviewer's reading of the demo log is right.) |
| 7 | Demo prose contradicts demo log | **CONFIRMED** | `amt_token_economy_demo.py:209-211` prints "couldn't afford GPT-4 (needs 3 beta, had 1)" after the call log records `success`. |
| 8 | Copying an agent allows both copies to pay | **CONFIRMED — reproduced ×4** | `verify_02`: `copy.deepcopy(agent)` → copy A `success`, copy B `success` against the same gateway. Reviewer's harness (§1.9) identical under 3.14/46.0.4, 3.10/50.0.1 and 3.10/3.4.8. |
| 9 | 12 beta layers stripped in one visit (overcharge) | **CONFIRMED — reproduced ×4** | `verify_02`: 12 → 0 beta layers, `outcome=success`. Reviewer's harness: `twelve_beta_call = {layers_charged: 12, success: true}`. |

### 1.3 Cross-organizational accountability

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 10 | "Public ledger" is a mutable in-memory list; commitments unsigned, unanchored | **CONFIRMED** | `amt_extensions.py:304-318` `PublicLedger.commitments: list[PublicCommitment]`; `publish()` is `append` (docstring says "Immutable once published" — nothing enforces it). No signing or external anchoring anywhere in the module (grep `sign|anchor` → only the docstring word "anchor trust" at `:309` and `time.time()` timestamps). |
| 11 | Honest-environment assumption collides with "without trust" | **CONFIRMED** (wording) | Paper states the assumption honestly at `paper/agentropy.md §11.1` and `paper/cross_org_accountability.md:430-438` (which even lists "Clone the agent (copy layers before decrypting)" as a malicious-environment move — i.e. the paper already names item 8's attack and scopes it out). The collision is with the cross-org paper's *title* ("…Without Trust"), `:142` "**Non-repudiation**: The operator cannot deny a committed transaction", `:236` "Zero Trust", and `:476` "No trust, no protocol, no consensus mechanism, no identity provider." |
| 11a | Merkle commitments cannot prove the interaction happened, honest reporting, completeness, authorization-at-time, or non-regeneration (review §"A Merkle Root Is a Witness, Not a Judge", five bullets) | **CONFIRMED** (architectural) | Commitment covers hashes of operator-created `LedgerEntry` records (`amt_extensions.py:219` entry ids are `os.urandom`); no signer, no policy state, no completeness proof, no attestation. `:438` in the paper concedes "does not prevent real-time lying". The one thing the root *does* prove — consistency with a root that was independently preserved — the reviewer grants. |

### 1.4 Physical IoT

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 12 | Encode/decode round trip is not invertible | **CONFIRMED — reproduced to 3 decimals, ×4** | `verify_01`: 50 Wh → 45.396; 100 MB → 128.000; 500 ops → 453.960; 30 s → 26.984; 50 reads → 43.820. Reviewer's harness identical under all three environments. Causes: GCM overhead (28 B/layer) inflates decoded mass; `to_layer_specs` quantises to 256-B layers and caps payloads at 512 B (`amt_physical_iot.py:228-240`). Contradicts `paper/physical_iot.md:55-58` "This mapping is bidirectional" and `:88` "knows exactly what physical resources remain". |
| 13 | Scale demo builds a fresh topology per agent; no shared depletion | **CONFIRMED** | `amt_physical_iot_demo.py:405` `topo = build_route_topology()` inside the per-agent loop. Contradicts `paper/physical_iot.md:135` "As battery depletes at a location (from previous agents consuming it)". |
| 14 | — (reviewer did not say this) | **NUANCE** | The battery-dependent mass gate *is implemented* (`amt_physical_iot.py:139-164`, recomputed per visit at `:435-437`). The reported run never exercises it across agents. Correct phrasing: "implemented, not exercised in the reported experiment" — not "absent". **Round 2 sharpening (§2.4): it cannot bind in the configured demo at all.** |
| 15 | "Battery budget directly predicts survival distance" printed regardless of result | **CONFIRMED — reproduced ×2** | `amt_physical_iot_demo.py:488-491` is unconditional. Live run (Zenodo bytes): all four battery tiers → 0 survivors, avg 5.0 locations; totals 150 agents / 750 interactions / 32,486 layers / 0 violations — identical to the paper's §5.3 table (the demo is seeded, `rng = random.Random(42)` at `:378`). |

### 1.5 Marketplace / ecology

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 16 | Regeneration clock starts at sim-time 0 while `last_tick` defaults to wall-clock, so elapsed clamps to zero and "passive regeneration does not occur during the simulation" | **OVERSTATED** | `amt_marketplace.py:64` `last_tick = field(default_factory=time.time)`; `:72-76` `elapsed = max(0, now - last_tick)` then `last_tick = now`. Only the **first** `tick()` loses its regeneration; it rebases `last_tick` to sim-time and every later tick regenerates normally. `verify_03` (through `MarketplaceTopology.tick`, pool `current=0`, rate 10/s, 0.5-s ticks): 0.0 → 5.0 → 10.0 → 15.0. With `max_steps=30` (`:355`) the simulation regenerates for 29 of 30 ticks. **It is a one-tick offset bug, not absent regeneration.** *Why the reviewer saw zero:* his harness calls `topology.tick(10)` exactly **once** (`2026-08-21-agentropy-targeted-verification.py:79`) and reads `pool.current` — that single tick is the one that is lost. `pool_after_ten_simulated_seconds = 0` reproduces here too (§1.9); a second `tick(10)` would show 100. Factual correction to request. |
| 17 | Nutrient cycler counts the entire budget as cycled while accreting at most three layers | **CONFIRMED** | `amt_marketplace.py:171` `self._total_cycled += budget`; `:282` `for kc_name, payload in new_specs[:3]`. |
| 18 | No system-level equation connects removed mass to factory-created mass; 300 B budget → 356 B (2 classes) / 440 B (5 classes) | **CONFIRMED — reproduced ×3** (round 1 had read it only) | Reviewer's harness (§1.9): `"2": {generated_layers: 2, generated_ciphertext_mass: 356}`, `"5": {generated_layers: 5, generated_ciphertext_mass: 440}` for `nutrient_budget: 300` — identical under all three environments. `NutrientCycler.cycle()` creates layers via `factory.create_layer`, each carrying fresh 28-B GCM overhead; nothing reconciles against what was deposited. |
| 19 | No reproduction; population can only stay level or decline; "carrying capacity" is a tail average; "speciation" is predefined profiles | **CONFIRMED** | `amt_marketplace.py:533-542` `carrying_capacity_estimate` = mean of the last 30 % of alive counts; no agent-creation path in `run_population` (`:389-466`). `amt_marketplace_demo.py:378-412` constructs the two profiles; `:445-449` prints "Alpha-heavy agents thrive at feeding_a … Beta-heavy agents thrive at feeding_b" unconditionally. |
| 19a | Speciation outcome varies run to run (reviewer: 0/0, then 2/1) | **CONFIRMED — reproduced ×3** | Three runs of `amt_marketplace_demo.py` on the Zenodo bytes: alpha-heavy survivors **2 / 0 / 1** (beta-heavy figures in `demo-out/marketplace_run{1,2,3}.txt`); speciation-demo survival 5/50, 4/50, 2/50; scale-run interactions 2,135 / 2,035 / 2,004 (paper: 2,095); recycling rate 76.9 % / 76.7 % / **40.8 %** (paper: 77.3 %); estimated carrying capacity 3 / 2 / 3 (paper: "4-6"). The "thrive" line printed in all three. |

### 1.6 Ablation

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 20 | Random condition removes ~1 layer per env key rather than all matching | **CONFIRMED** | `amt_ablation.py:112-113` `n_to_remove = max(1, min(env.hazard_classes, len(agent.layers)))`. The in-code comment *intends* parity with control ("Match control's stripping rate: ~1 layer per env key class"); parity only holds when agents carry ≤1 layer per class. |
| 21 | Random condition invents a 50/50 signal/loss split | **CONFIRMED** | `amt_ablation.py:128-129` `signal = consumed // 2; loss = consumed - signal`. |
| 22 | Immortal condition returns zero signal by construction | **CONFIRMED** | `amt_ablation.py:65-76` hard-codes `total_signal=0`. |
| 23 | Stratification's 3:1 ratio is an input construction | **CONFIRMED** | `amt_ablation.py:279-297` rich = 4 data layers × 3 classes; poor = 4 data alpha + 4 empty beta + 4 empty gamma. The paper says as much (`paper/agentropy.md` §9.4 "matching the 3:1 key-class breadth ratio") but then calls the result "establishes necessity". |
| 23a | Ablation numbers reproduce | **CONFIRMED — reproduced** | `amt_ablation_demo.py` on the Zenodo bytes: 561/2,000/1,300 interactions; 768/256 B → 3.00×, 138/73 B → 1.90×; niche scores 1.00/0.00/0.00; 41,000/0/11,240 B — every cell identical to the paper's §9.4 tables. (Seeded: `random.seed(42)`.) |

### 1.7 Reproducibility

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 24 | Results vary across processes under different `PYTHONHASHSEED` | **CONFIRMED — reproduced, root-caused** | Round 2, Zenodo bytes, seeds 0/1/2: total tool calls **2,125 / 2,108 / 2,093**; successful **444 / 453 / 451**; survivors **107 / 98 / 88** (paper: 2,113 / 449 / 91; reviewer: 2,090–2,206 calls, 100–106 survivors). Round-1 figures identical for seed 0. **Root cause:** `amt_extensions.py:841` `Topology.reachable_from` iterates `self.edges[node_id]`, a `set[str]` — neighbour order depends on the string hash seed, and `AgentBehavior.choose_node` (`:739-747`) does a cumulative weighted draw over `scored` **in list order**, so the same `random.uniform` draw selects a different node when the order changes. All `random` calls are seeded (`amt_token_economy_demo.py:380,406`); `os.urandom` payloads do not change lengths. One `sorted()` restores determinism. |
| 25 | Not a Python-version effect (author's check, not reviewer's) | **CONFIRMED** | Same demo under 3.10.20 → 448 / 104; 3.12.13 → 444 / 107; 3.14.7 → 444 / 107 (seed 0). |
| 26 | No test suite, dependency manifest, repeated-trial distributions, or CIs | **CONFIRMED** | Zenodo zip file list (§0): 25 files, no `requirements*`, `pyproject*`, `tests/`, `.github/`. README says `pip install cryptography` unpinned. |
| 26a | 50,000-agent scale run: reviewer 280.77 s, 2,286,167 summed node visits, 0 assertion failures | **CONFIRMED — reproduced** | `PYTHONHASHSEED=0 python3 amt_scale.py --agents 50000 --steps 50 --workers 4` on the Zenodo bytes: 334.31 s, survival 90.0 % (44,975), node visits 718,499 + 671,737 + 473,668 + 421,625 = **2,285,529**, `Violations: 0`. Visit total differs from the reviewer's by 638 (0.03 %) — same `set`-iteration cause as item 24 (the scale harness seeds `random` per agent, `amt_scale.py:262`, but neighbour order is still hash-seed dependent and the reviewer's interpreter differs). Full output: `demo-out/../scale_run.txt`. |
| 26b | Cross-org demo (paper: 200 agents, 457 interactions, 28.5 % validated) | **NUANCE** | Zenodo bytes, default hash seed: 200 agents, **459** interactions, 0 violations, 58 validated (29.0 %) / 142 skipped (71.0 %). Same process-sensitivity as item 24; the paper's integers are one draw. |

### 1.8 Interpretive claims about the paper

| # | Reviewer's claim | Verdict | Receipt |
|---|---|---|---|
| 27 | The papers claim a "substrate-independent law of life" / "general theory of life-like dynamics" | **OVERSTATED** | `paper/agentropy.md:604` (Appendix C): *"This paper makes only the weaker, testable claim (a necessary condition for life-*like* dynamics); the stronger claim is argued in companion work."* Appendix C opens (`:596`): *"none of this paper's empirical claims depend on them."* The deposited paper's claim is the necessary-condition claim in `§7.4` and `§13` (and the title). The review's "smaller than a substrate-independent law of life" and its opening "general theory of life-like dynamics claimed by the papers" attribute a deferred claim to v1.0.0. Ask that the hedge be preserved. |
| 28 | The paper claims cryptographic scarcity / no double-spending | **CONFIRMED** | `paper/agentropy.md:250` "Conservation eliminates inflation, double-spending, and unauthorized access because mass is physical"; `:88` "(cannot be inflated, counterfeited, or double-spent)"; `paper/token_economy.md:12` "ensures that mass cannot be created, double-spent, or inflated"; `:280-282` §8.2 "No Double-Spending". `paper/agentropy.md:389` "AMT tokens (layers) cannot be duplicated because they are AES-256-GCM ciphertexts, whereas Petri net tokens are abstract and can be trivially copied" — the exact inversion of item 4. These sentences are wrong as written and need rewriting, not defending. |
| 29 | "Agentropy contains roughly 11,500 lines of Python and paper text" | **CONFIRMED** | `wc -l paper/*.md *.py` = 11,545 (matrix row 3). |
| 30 | "The code ran without modification under Python 3.10.12 with `cryptography` 3.4.8" | **CONFIRMED** (3.4.8 on 3.10.20) | Reviewer's harness ran unmodified under `uv run --python 3.10 --with cryptography==3.4.8` (§1.9, run C). |

**Score, round 2:** 34 checked items (28 round-1 items + 11a, 19a, 23a, 26a, 26b, 29, 30, minus none). **31 CONFIRMED**, **2 OVERSTATED** (#16, #27), **3 NUANCE** (#14, #26b, and #14's sharpening in §2.4), **0 NOT-REPRODUCED**. Every claim in the review's eleven sections and every row of the evidence matrix (§1.10) now has a verdict and a receipt.

### 1.9 The reviewer's harness — verbatim results

`python3 2026-08-21-agentropy-targeted-verification.py <extracted Zenodo zip>` — no source modified. Output was **byte-identical** (same JSON, `sort_keys=True`) across all three runs:

| Run | Interpreter | `cryptography` | Exit |
|---|---|---|---|
| A | Python 3.14.7 (Homebrew) | 46.0.4 | 0 |
| B | Python 3.10.20 (`uv`) | 50.0.1 | 0 |
| C | Python 3.10.20 (`uv`) | **3.4.8** (reviewer's version) | 0 |

```json
{
  "copied_state_calls": [
    {"layers_charged": 1, "success": true},
    {"layers_charged": 1, "success": true}
  ],
  "declared_llm_cost": 3,
  "nutrient_cycle_by_key_class_count": {
    "2": {"generated_ciphertext_mass": 356, "generated_layers": 2, "nutrient_budget": 300},
    "5": {"generated_ciphertext_mass": 440, "generated_layers": 5, "nutrient_budget": 300}
  },
  "physical_budget_interpreted": {"bandwidth": 128.0, "battery": 45.396, "cpu": 26.984, "sensor": 43.82, "storage": 453.96},
  "physical_budget_requested": {"bandwidth_mb": 100, "battery_wh": 50, "cpu_seconds": 30, "sensor_reads": 50, "storage_ops": 500},
  "pool_after_ten_simulated_seconds": 0,
  "twelve_beta_call": {"layers_charged": 12, "success": true}
}
```

Every figure in the review's tables that the harness produces is reproduced exactly. The one interpretive gap is `pool_after_ten_simulated_seconds: 0`, which is the first-tick loss of item 16, not "no regeneration".

Existing scripts, round 2 (Python 3.14.7 / 46.0.4, worktree at `8fca48b`): `verify_01` → died_paying / died_paying (no ballast), 12→0, regen 0.0/5.0/10.0/15.0, IoT 45.396/128.000/453.960/26.984/43.820. `verify_02` → success / success, 12→0 success. `verify_03` → 0.0/5.0/10.0/15.0. All exit 0. Identical to round 1.

### 1.10 Evidence-matrix rows → verdicts

The reviewer's internal matrix has 23 rows. Mapping to the items above (all matrix "Verified"/"Reproduced" statuses hold unless noted):

| Matrix row | Item(s) | Verdict |
|---|---|---|
| Artifact citable and versioned | §0 | CONFIRMED |
| Reviewed archive matches deposit (md5 `6a2315…`) | §0 | CONFIRMED — and extended: file-by-file sha256 identity with tag `v1.0.0` |
| ~11,500 lines | 29 | CONFIRMED |
| All advertised demos runnable | 15, 19a, 23a, 26a, 26b | CONFIRMED (5 demos + scale, exit 0) |
| Invariant survives 50,000 agents | 26a | CONFIRMED |
| Equation is definitional in v1 | 1 | CONFIRMED |
| AES-GCM does not make ciphertext non-copyable | 4 | CONFIRMED |
| Copied-state double spending | 8 | CONFIRMED |
| Declared prices not enforced | 5, 6, 7 | CONFIRMED |
| A visit removes all matching layers | 3, 9 | CONFIRMED |
| Public ledger mutable, in-memory | 10 | CONFIRMED |
| Merkle commitments don't prove authorization/execution/completeness | 11a | CONFIRMED |
| Key-class existence not hidden | 2 | CONFIRMED |
| Physical encoding not invertible | 12 | CONFIRMED |
| Physical scale demo has no shared depletion | 13, 14 | CONFIRMED + NUANCE (gate implemented; cannot bind — §2.4) |
| No battery-dependent survival distance shown | 15 | CONFIRMED |
| Marketplace regeneration does not occur | 16 | **OVERSTATED** — one-tick offset; 29 of 30 ticks regenerate |
| Nutrient cycling not globally conservative (300→356/440) | 17, 18 | CONFIRMED — reproduced |
| No reproduction or speciation | 19 | CONFIRMED |
| Speciation narrative unconditional | 19, 19a | CONFIRMED — reproduced (2/0/1 across three runs) |
| Carrying capacity is a tail average | 19 | CONFIRMED |
| Ablation does not hold depletion constant | 20–23 | CONFIRMED |
| Results process-sensitive | 24, 25 | CONFIRMED — root-caused |
| No test suite / manifest | 26 | CONFIRMED |

Of the matrix's six "Interpretive Judgments Requiring Author Review", none is a factual claim; they are handed to the author as questions in the dossier (`docs/review/OVERMIER-RESPONSE-DOSSIER.md` §3).

---

## 2. Findings beyond the review

1. **Nondeterminism root cause** (item 24): `set` iteration in `Topology.reachable_from`, `amt_extensions.py:841`, combined with the order-dependent cumulative draw in `choose_node` (`:739-747`). Also `amt_core.py:267` returns `set(self.secrets.keys())` for hazard classes — harmless today (only used for counts/membership) but worth sorting for the same reason.
2. **`ResourcePool.regenerate(current_time)` uses `current_time or time.time()`** (`amt_marketplace.py:72`): a sim-time of exactly `0.0` silently falls back to wall-clock. Latent; fix alongside item 16.
3. **The "immortal" ablation condition is the copy-attack regime.** The proper control for "depletion" is *decrypt without destroy* — extract signal, keep the layer. That is exactly what a cloned agent gets (item 8). Reframed this way, the reviewer's double-spend finding and the ablation are the same experiment: without enforced destruction, signal is unbounded and the stratification/selectivity results dissolve. This is a v2 design point, not a v1.0.1 fix, but it is the honest way to state what the ablation *does* show.
4. **The IoT mass gate cannot bind in the configured demo** (sharpens item 14; the reviewer did not say this). The tightest gate is 500 KB (`amt_physical_iot.py:161-162`, `500 * 1024 = 512,000 B`). The heaviest agent `demo_6_scale` can build (60 Wh / 80 MB / 300 ops / 25 s / 40 reads, the top of every `rng.uniform` range at `amt_physical_iot_demo.py:391-395`) has mass **94,461 B**; the paper's §5.1 agent is 106,603 B. Both are under the floor by ~5×, so "Dynamic load-shedding … Heavier agents get blocked" (`paper/agentropy.md` §5.3; `paper/physical_iot.md:135`) is not exercised by *any* agent in *either* experiment, shared topology or not. Script: `iot_gate_check.py`. Fixing item 13 (shared topology) makes the battery deplete across agents but still cannot make the gate bind; that needs either heavier agents or lower thresholds, which is an experiment-design change (v2), not a patch.
5. **The paper already names the clone attack and scopes it out** (`paper/cross_org_accountability.md:435` "Clone the agent (copy layers before decrypting)") — under the honest-environment assumption. The token paper then claims the opposite (`token_economy.md:282`). The two papers disagree with each other; the cross-org one is right.
6. **Reviewer's regeneration test is single-tick** (item 16 receipt). Worth stating in the response because it explains, without blame, why a careful reviewer concluded "does not occur".

---

## 3. Scope for v1.0.1 (patch)

Semantic-versioning patch: **fixes and corrections only.** No uniqueness, settlement, signing, or external anchoring — those change the threat model and belong to v2 with their own design record. A new Zenodo version deposit will mint a version DOI under the existing concept DOI; the v1.0.0 DOI stays immutable and the review keeps pointing at it.

### 3.1 Code fixes

| Priority | Fix | Files | Closes item(s) | Reviewer rec. |
|---|---|---|---|---|
| P0 | Determinism: `sorted()` neighbour iteration; sort hazard-class sets | `amt_extensions.py:841`, `amt_core.py:267` | 24 | #8, #10 |
| P0 | Gateway price enforcement: select exactly `base_cost` layers of the tool class; reject underfunded payment *before* tool execution; outcome `insufficient_funds` | `amt_token_economy.py:165-215`; needs a bounded-count variant of `interact()` in `amt_core.py` | 3, 5, 6, 7, 9 | #4 |
| P1 | Marketplace regeneration clock: initialise `last_tick` from sim-time (set on `add_node`); remove the `or` fallback | `amt_marketplace.py:64, 72` | 16, §2.2 | — |
| P1 | Nutrient accounting: `_total_cycled` counts only what was actually accreted; return unused budget to the pool; report created overhead | `amt_marketplace.py:171, 282` | 17, 18 (measured, not enforced) | #7 (partial) |
| P1 | Remove unconditional "KEY INSIGHT" prints, or compute them from the measured result (survival-distance, "thrive", "could not afford") | `amt_physical_iot_demo.py:488`, `amt_marketplace_demo.py:445-449`, `amt_token_economy_demo.py:207-219` | 7, 15, 19 | #9 |
| P1 | IoT scale demo: one shared topology across agents; report decoded-vs-requested budget error and gate-blocked count in the demo output | `amt_physical_iot_demo.py:405` | 12, 13, 14, §2.4 | — |
| P2 | Ablation controls: random condition removes the *same count* the control would; derive signal/loss from actual decryption of the removed layers instead of `// 2` | `amt_ablation.py:112-131` | 20, 21 | #8 |
| P2 | `requirements.txt` / `pyproject.toml` pinning `cryptography`; `tests/` turning the headline assertions into pytest (conservation identity, price enforcement, determinism across `PYTHONHASHSEED`, regeneration after N ticks, copy-replay **documented as a known limitation test**, not a pass); CI | repo root | 26 | #10 |
| P2 — deferred | Multi-seed runner: N seeds → mean ± CI for calls/survivors | — | 24, 26 | #8 — v1.0.1 records the observed range in the errata instead |
| — not a fix | Stratification fixture (item 23): the 3:1 is by construction and the paper says so; the correction is wording (§3.2), not a fixture change (that would be a new experiment) | — | 23 | #8, #9 |

### 3.2 Paper wording corrections (same release)

| File:line | Current | Problem | Direction |
|---|---|---|---|
| `paper/token_economy.md:282` §8.2 | "The encrypted form is gone. An agent cannot present the same layer twice" | False — item 8 | State: destruction is local to the holder's process; uniqueness across copies requires an authority outside the scheme (v2). |
| `paper/token_economy.md:12` abstract; `:50` | "cannot be created, double-spent, or inflated"; "Trust is unnecessary" | Items 8, 28 | Narrow to "cannot be created outside the factory"; drop "double-spent". |
| `paper/agentropy.md:250`; `:88` | "eliminates inflation, double-spending, and unauthorized access because mass is physical"; "cannot be inflated, counterfeited, or double-spent" | False — items 8, 28 | Narrow to what holds: no mass creation outside the factory; depletion is irreversible *within an honest process*. |
| `paper/agentropy.md:389` §10.1 | "AMT tokens (layers) cannot be duplicated because they are AES-256-GCM ciphertexts" | Inverts item 4 | Ciphertexts are bytes and copy like any bytes; what AES-GCM gives is confidentiality + integrity, not uniqueness. |
| `paper/cross_org_accountability.md:94, 97` | "cannot even detect the existence of beta layers" | False — item 2 | Either encrypt the class tag (v2) or restate: class *presence* is visible, class *content* is not. |
| `paper/cross_org_accountability.md` title, `:142`, `:236`, `:476` | "Without Trust"; "Non-repudiation"; "Zero Trust"; "No trust, no protocol…" | Collides with `:430-438` — item 11 | "Without a trusted intermediary *for the arithmetic*" — each org verifies its own consumption; cross-party non-repudiation is out of scope for the reference implementation. |
| `paper/token_economy.md:103, 297, 303` | "exactly 1 LLM inference call"; "costs exactly 3 layers"; "exactly 4 LLM calls" | False until P0 price enforcement lands — items 3, 5 | Becomes true after the fix; keep, cite the enforcing code. |
| `paper/token_economy.md:224` §7.2 | "partially pays for GPT-4 (1 beta layer stripped, but needs 3 — partial payment, tool still fires)" | The paper *documents* item 6 as intended behaviour | After the fix: rejected as `insufficient_funds`; update the scenario and the demo. |
| `paper/physical_iot.md:55-58, 88` | "This mapping is bidirectional"; "knows exactly what physical resources remain" | Item 12 | "Approximately, within the quantisation and overhead error reported by the demo" + the measured table. |
| `paper/physical_iot.md:135`; `paper/agentropy.md` §5.3 "Dynamic load-shedding" | "from previous agents consuming it"; "Heavier agents get blocked" | Items 13, §2.4 | Shared topology makes the first true; the second is not exercised by any agent in the reported experiments — say so. |
| `paper/agentropy.md §8.1` table; `§4.4`, `§6.4`; `token_economy.md §7.3`, App. B; `marketplace.md §6` | Single-run integers (2,113; 91; 2,095; 77.3 %…) | Items 24, 19a, 26b | Label as one reference run; add the observed cross-process range from these notes. |
| `paper/agentropy.md §9`, §9.6, §13 | "establishes necessity" | Items 20–23 | "consistent with"; keep "necessary condition" as the hypothesis, not the result, unless the repaired ablation supports it. |
| `paper/agentropy.md §6`, `marketplace.md` | "carrying capacity", "speciation", "boom/bust", "Gause's competitive exclusion" | Item 19 | Use "tail-average population", "niche-differential survival", "monotonic decline" until reproduction exists. |
| `paper/agentropy.md` Appendix C | — | — | **Unchanged, verbatim.** It is the hedge the review missed (item 27). |

### 3.3 Explicitly out of scope for v1.0.1

- Uniqueness / anti-replay (signed capabilities, settlement) — reviewer recs #3, #6. Threat-model change → v2 + design record.
- Hiding key classes cryptographically — rec #5. v2.
- Global mass equation across factory/accretion/pools — rec #7. v2 (v1.0.1 *measures* and reports created overhead without *enforcing* a global equation).
- Reproduction in the ecology model — `§12.1` future work. v2.
- Renaming the central result — rec #1. Author's call; wording, not code.
- Making the IoT mass gate bind (heavier agents or lower thresholds) — experiment redesign, v2.

---

## 4. Inputs for the author response (facts only; prose is the author's)

**Concede outright (all verified):** items 2, 3, 4, 5–9, 10, 11, 11a, 12, 13, 15, 17, 18, 19, 19a, 20–24, 26, 26a, 28, 29, 30. Accept "major revision".

**Request factual correction:**
- Item 16 — regeneration is a one-tick offset, not absent; 29 of 30 ticks regenerate; the harness's single `tick(10)` is the tick that is lost. Receipt: `verify_03_regen_topology.py`; reviewer's own harness line 79.
- Item 27 — v1.0.0 explicitly makes only the necessary-condition claim and defers the definition-of-life claim to companion work (`paper/agentropy.md` Appendix C, `:596`, `:604`). Preserve the hedge.

**Add nuance:** item 14 / §2.4 — the battery gate mechanism exists; the reported run doesn't exercise it, and *cannot*, because the gate floor is ~5× the heaviest agent. Item 26b — cross-org integers are one draw too.

**Offer as author's own findings:** the `set`-iteration root cause (item 24) and the Python-version check (item 25) — the reviewer reported the symptom; the cause is now known and the fix is one line. §2.4 (gate cannot bind) and §2.5 (the two papers disagree with each other about cloning) — the reviewer did not find these; the author reports them himself.

**Post-v1 work, to be attributed separately (per the reviewer's request):** see the dossier §4. None of it is in v1.0.0 and none of it rescues v1.0.0's claims.

---

## 5. Verified in round 2 (previously open)

- Reviewer's attachments obtained and run against the Zenodo bytes under three environments including his exact `cryptography` 3.4.8 — §1.9.
- Nutrient test figures (300 B → 356 B two-class; 440 B five-class) reproduced ×3 — item 18.
- Marketplace speciation run-to-run variance re-run ×3 — item 19a.
- 50,000-agent scale run re-run (334.31 s; 2,285,529 node visits; 0 violations) — item 26a.
- `paper/marketplace.md` and `paper/physical_iot.md` read end-to-end; additional wording the fixes invalidate is in §3.2.
- Zenodo ↔ tag identity — §0.

**Still open / not attempted:** none of the review's claims. The reviewer's exact interpreter build (3.10.12) was not installed; 3.10.20 with his `cryptography` 3.4.8 was used instead (§1.9 run C) and produced identical output.

## 6. Reproduction commands

```bash
# from the worktree root
bash docs/reviews/2026-08-22-overmier-v1.0.0/identity_proof.sh          # Zenodo <-> tag identity (downloads the zip)
python3 docs/reviews/2026-08-22-overmier-v1.0.0/verify_01_replay_regen_iot.py
python3 docs/reviews/2026-08-22-overmier-v1.0.0/verify_02_replay_with_ballast.py
python3 docs/reviews/2026-08-22-overmier-v1.0.0/verify_03_regen_topology.py
python3 docs/reviews/2026-08-22-overmier-v1.0.0/iot_gate_check.py
# the reviewer's harness, against an extracted copy of the Zenodo zip (path from identity_proof.sh)
python3 /path/to/2026-08-21-agentropy-targeted-verification.py /path/to/nwalker85-agentropy-91df6c0
uv run --python 3.10 --with 'cryptography==3.4.8' python /path/to/2026-08-21-agentropy-targeted-verification.py /path/to/nwalker85-agentropy-91df6c0
for s in 0 1 2; do PYTHONHASHSEED=$s python3 amt_token_economy_demo.py | grep -E 'Total tool calls|Successful calls:    |Agents surviving'; done
for i in 1 2 3; do python3 amt_marketplace_demo.py | grep -A4 'SPECIATION RESULTS' | grep -E 'Alpha-heavy|Beta-heavy'; done
PYTHONHASHSEED=0 python3 amt_scale.py --agents 50000 --steps 50 --workers 4
```

Round-2 raw outputs (demo logs, harness JSON ×3, scale log) are kept in the session scratchpad and summarised above; the scripts regenerate them.
