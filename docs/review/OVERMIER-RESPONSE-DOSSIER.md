# Overmier review — response dossier

**What this is.** The receipts pile Nate writes the author response *from*. It is organised in the four buckets Kurt asked for on 2026-08-22 and nothing here is addressed to Kurt. Verdicts and receipts come from `docs/reviews/2026-08-22-overmier-v1.0.0/VERIFICATION-NOTES.md` (item numbers below refer to its tables); what changed in the paper and code is in `paper/ERRATA-v1.0.1.md` (E-/F-numbers). Attribution inline: **[NW]** Nate, **[KO]** Kurt, **[CS]** the author's agent (this document, RAV-1703, 2026-09-04/05).

**Artifact identity.** Kurt reviewed the public deposit only. The Zenodo zip (`md5 6a2315a50bbb2d49dd1db9aa8e195785`) is file-for-file sha256-identical to tag `v1.0.0` = `main@91df6c0` (25/25 files). Every round-2 run below executed against the downloaded bytes. His harness produced byte-identical JSON under Python 3.14 / `cryptography` 46.0.4, Python 3.10 / 50.0.1, and Python 3.10 / **3.4.8** (his exact library version).

**Totals.** 34 checked items: **31 CONFIRMED, 2 OVERSTATED, 3 NUANCE, 0 NOT-REPRODUCED.** Every claim in the review's eleven sections and every row of the 23-row evidence matrix has a verdict and a receipt. His recommendation — *major revision* — is supported by the verification.

---

## 1. Factual corrections

Two statements in the review are wrong about v1.0.0. Everything else he says about the code held.

### 1.1 Marketplace regeneration is a one-tick offset, not absent — item 16 (OVERSTATED)

**Review text it corrects** (section "The Marketplace Is a Declining Cohort, Not Yet an Ecology", first problem): *"the simulated regeneration clock begins at zero while each resource pool's last-update time begins as a Unix wall-clock timestamp. Elapsed time is clamped at zero, so the advertised passive regeneration does not occur during the simulation."* Evidence matrix row: *"Marketplace regeneration does not occur with the current clocks … direct test left an empty pool at zero after a simulated tick."*

**What the code does** (`amt_marketplace.py:64, 72-76` at v1.0.0): `last_tick` defaults to `time.time()`; `regenerate()` computes `elapsed = max(0, now − last_tick)` **and then sets `last_tick = now`**. The first simulation tick loses its regeneration; every later tick regenerates normally. With `max_steps=30` the simulation regenerates for 29 of 30 ticks.

**Receipts.** `verify_03_regen_topology.py` on v1.0.0: pool at 0.0 → 5.0 → 10.0 → 15.0 over four 0.5-s ticks (rate 10/s). **Why Kurt saw zero:** his harness calls `topology.tick(10)` exactly once (`2026-08-21-agentropy-targeted-verification.py:79`) and reads the pool — that single tick is the lost one. His `pool_after_ten_simulated_seconds: 0` reproduces here; a second `tick(10)` reads 100. Fixed in v1.0.1 (F3, `689dc0f`); his harness on the patched tree reads `100`.

**Honest framing for the response [CS]:** his description of the *mechanism* (wall-clock default vs simulation time) is exactly right; the *conclusion* ("does not occur") is wrong by 29 ticks. Stated without blame it explains why a careful single-tick probe reached it.

### 1.2 v1.0.0 does not claim a "substrate-independent law of life" — item 27 (OVERSTATED)

**Review text it corrects.** Opening summary: *"It does not yet establish a new conservation law, cryptographic scarcity, trustless accountability, or general theory of life-like dynamics claimed by the papers."* Section "What I Think Agentropy Actually Is": *"That is smaller than a substrate-independent law of life."*

**Paper text he missed** — `paper/agentropy.md` Appendix C, unchanged in v1.0.1:

> "This paper isolates one empirical claim: structured, irreversible depletion as a *necessary condition* for life-like dynamics. That claim is the core of a larger framework, **Agentropy**, developed in companion work. We sketch the connections here for context; **none of this paper's empirical claims depend on them.**"
>
> "**The definition of life.** … This paper makes only the weaker, testable claim (a *necessary condition* for life-*like* dynamics); the stronger claim is argued in companion work."

The title, §1.1, §7.4 and §13 all state the necessary-condition claim and disclaim sufficiency. The "law of life" is explicitly deferred. **The hedge is preserved verbatim in v1.0.1** (Appendix B and C diffed against `91df6c0`: identical).

**What he is right about in the same breath [CS]:** "cryptographic scarcity" and "trustless accountability" *are* claimed in v1.0.0 (items 28, 11) and are wrong; only the third phrase attributes a deferred claim.

### 1.3 Nuances (accurate, but incomplete)

| Item | His statement | What to add |
|---|---|---|
| 14 / §2.4 | The scale demo "constructs a fresh five-location topology for every agent. Agents therefore do not deplete a shared environment." | True (`amt_physical_iot_demo.py:405`, fixed F5). **Also true, and his review does not say it [CS finding]:** the tightest mass gate is 512,000 B and the heaviest agent either experiment can build is 94,461 B (scale demo) / 106,603 B (§5.1 agent), so the gate cannot bind for any agent regardless of sharing. Blocked count after the fix: 0 of 750. This is the author's own disclosure. |
| 26a | 50,000-agent run: 280.77 s, 2,286,167 node visits, 0 failures | Reproduced: 334.31 s, **2,285,529** visits, 0 violations. The 638-visit difference is the same hash-seed ordering bug as item 24, on a different interpreter. |
| 26b | (not raised) | The cross-org integers (457 interactions, 28.5 %) were also one process-dependent draw; v1.0.1 gives 459 / 29.0 % deterministically. |
| 29, 30 | ~11,500 lines; ran unmodified on 3.10.12 / 3.4.8 | Both confirmed (11,545 lines; 3.4.8 on 3.10.20 here). |

### 1.4 Things he found that Nate concedes outright (all reproduced)

Items 1–13, 15, 17–26, 28: the identity is definitional (and the paper's Appendix B says so); `key_class` is plaintext; every matching layer is stripped; consumption is a list reassignment; the gateway never consulted `base_cost`; a 1-layer payment was recorded as a successful 3-layer call and the demo prose contradicted its own log; copied agents both pay; 12 layers were charged for one call; the public ledger is an unsigned in-memory list; "without trust" collides with the stated honest-environment assumption; the IoT round trip is lossy to the third decimal he reported; "predicts survival distance" printed unconditionally over a run with 0 survivors in every tier; the cycler counted budget not delivery (300 B → 356 B / 440 B reproduced); no reproduction, tail-average "carrying capacity", predefined "species", unconditional "thrive"; all four ablation confounds; hash-seed nondeterminism; no tests, manifest, or intervals.

**Author's own findings to offer alongside (not in the review):** the root cause of item 24 (`set` iteration in `Topology.reachable_from` + order-dependent draw in `choose_node`; one `sorted()` fixes it); the gate-cannot-bind result (§1.3); the two papers disagreeing with each other about cloning (`cross_org_accountability.md` §9 lists it as an attack; `token_economy.md` §8.2 denied it); and — the largest — **with the RANDOM condition's invented 50/50 split replaced by real layer geometry, stratification under class-blind stripping is 3.12×, not 1.9×.** The "structure degrades stratification" result in v1.0.0 §9 was an accounting artifact. With the depletion rate matched (new RANDOM-MATCHED), stratification is 2.87× and the pure-class niche score is 1.00 — identical to CONTROL by construction. What survives the repaired controls: depletion is necessary for every dynamic measured; class-selective structure is necessary for per-class attribution. (Errata E12; `492b5fc`.) This goes further than his §"The Ablation Does Not Establish Necessity" and should be said plainly.

---

## 2. Misread intent / threat model

Places where the review reads a claim the paper did not make, or misses text that already concedes the point. Each with the paper text quoted. Where the paper *also* says the overclaim elsewhere, that is noted — the response should concede the sentence and point at the hedge, not defend the sentence.

### 2.1 The "law of life" — deferred, not claimed

Quoted in §1.2. The paper's claim is a necessary condition for life-*like* dynamics. Kurt's own review agrees this narrower claim is the interesting one ("The work gets more interesting when the claims get narrower"); the disagreement dissolves once Appendix C is read.

### 2.2 The threat model was stated — and then contradicted by headline sentences

**[KO]** rec #2: *"Define the threat model. State who can copy agents, mutate ledgers, control gateways, issue layers, and lie about execution."*

**Paper text he missed** — `paper/cross_org_accountability.md` §9 (v1.0.0 lines 430–438):

> "The current model assumes environments correctly implement the `interact()` function. A malicious environment could: Decrypt layers but report false signal/loss values; **Clone the agent (copy layers before decrypting)**; Inject layers without going through the accretion mechanism. Mitigation: The Merkle commitment to the public ledger makes post-hoc falsification detectable, but does not prevent real-time lying."

and `paper/agentropy.md` §11.1:

> "The conservation law is enforced inside the `interact()` function. A malicious environment that reimplements this function can report false signal/loss values. The law governs correct implementations; it does not detect incorrect ones."

So the cloning attack Kurt demonstrates was already named as out of scope. **What is not a misread:** the same deposit says "An agent cannot present the same layer twice" (`token_economy.md` §8.2), "cannot be inflated, counterfeited, or double-spent" (§4.3), "eliminates … double-spending" (§7.2), and "No trust, no protocol" (`cross_org` §10). Those sentences are wrong and v1.0.1 rewrites them (E1, E5). **The honest shape of the response [CS]:** the threat model existed in the limitations sections; the abstracts and conclusions claimed past it; v1.0.1 makes the limitations sections govern (E15 adds an explicit who-can-do-what paragraph).

### 2.3 "Tautology" — the paper said it first, and §8.3 gave the wrong reason

**[KO]** *"The paper eventually says this plainly: the conservation law is a tautology that 'holds because subtraction works.' That honesty is important."* — he credits Appendix B. **Where the misread is the paper's, not his [CS]:** `agentropy.md` §8.3 v1.0.0 said zero violations hold because "a violation would require AES-256-GCM decryption to produce bytes from nowhere — a cryptographic impossibility." That is the wrong reason; Appendix B is the right one. E13 fixes §8.3 to agree with Appendix B. Nothing to defend here; the response can simply agree.

### 2.4 Conservation is per-interaction by design; the global-mass sentence was the overclaim

**[KO]** *"nutrient cycling is not globally conservative … without a system-level equation connecting the removed mass to the created mass."*

**Paper text stating the intent** — `paper/marketplace.md` Appendix A, "Key design decisions": *"Conservation check skips accreted entries (accretion is separate from conservation)"*; §3.2: *"Agent B accretes new layers (separate from conservation)."* The design intent was always per-interaction conservation with accretion outside it. **What was the overclaim:** the next sentence, *"No mass is created from nothing"* — false at the system boundary (28 B of overhead per minted layer). E10 rewrites it; F4 fixes the budget-vs-delivery accounting (77.3 % → 29.3 %) and *reports* minted overhead. His rec #7 (a global mass equation) is v2 and is agreed.

### 2.5 Calibration was acknowledged; "bidirectional" was not

**[KO]** matrix caveat: *"The paper acknowledges calibration as future work, but also presents the mapping as bidirectional and exact in places."* Both halves are right: `physical_iot.md` §7.2 says *"Real-world calibration requires measuring actual resource consumption per layer interaction"*; §2.1 said *"This mapping is bidirectional."* E6 keeps the first and corrects the second with his table.

### 2.6 The budget observer was never meant to enforce — but the gateway was

**[KO]** *"The budget observer uses those numbers to report how many calls an agent can theoretically afford. The gateway does not enforce them."* `token_economy.md` §5.1 says of the observer: *"It does not enforce anything. The conservation law handles enforcement."* That is the intent he read correctly. What the paper *also* intended, and the code did not do, is the gateway charging its declared price (§4.1 `Gateway("GPT-4", key_class="beta", cost=3)`). Not a misread. Fixed (F2). **One thing worth saying [CS]:** after the fix, price enforcement is a *gateway rule* layered on the identity, not a consequence of the identity — v1.0.1 says so in §4.2 and §8.5 rather than re-attributing it to "physics".

### 2.7 What is *not* in v1.0.0 and must not be argued as if it were

The cube-protocol reading that custody is environmental (mass is traversed, not held — `~/docs/10-knowledge/ravenhelm/the cube protocol.md`, 2026-01-25) would answer Kurt's "encryption does not create scarcity" from a different direction. It is not in the deposit, it is a *reading of a downstream thesis* (cypher-mass capture §0c), and it belongs in §4 below, clearly dated, not here.

---

## 3. Substantive disagreements — questions for Nate

One question per item. The evidence on both sides is laid out; **the answers are not**. Where v1.0.1 already changed wording in the direction of one answer, that is flagged so Nate can revert it.

**Q1. Do you rename the central result?** [KO] rec #1: present it as "a typed accounting invariant or conservation-inspired resource model unless a falsifiable conservation claim can be formulated." *For:* Appendix B calls it a tautology; the identity cannot fail, so "zero violations" cannot be evidence for a law; "invariant" is what the code enforces. *Against:* the title's claim is "a conservation law **as a necessary condition**" — the word names the *mechanism* (structured irreversible depletion), and the necessity hypothesis is the falsifiable part; renaming the mechanism does not change the hypothesis. *v1.0.1 state:* title unchanged; §8.3 and the token paper's §10 now say "accounting identity"; §1.2 keeps "law" for the mechanism. **Your call: keep "conservation law" as the mechanism's name while narrowing what it is claimed to do, or rename it?**

**Q2. After the repaired ablation, is "necessary condition" still the thesis or a hypothesis?** *Evidence:* with honest signal accounting RANDOM stratification is 3.12× (v1.0.0: 1.90×); rate-matched RANDOM-MATCHED gives 2.87× and niche score 1.00; only per-class audit needs structure; IMMORTAL returns zero signal by construction (partly defined in). *For keeping:* depletion is necessary for every dynamic measured, and that is the thesis's core word. *Against "establishes":* structure's necessity does not survive for stratification or (pure-class) niches. *v1.0.1 state:* "establishes" → "is consistent with"; "both factors are necessary" withdrawn to hypothesis; §7.4 "we identify" → "we propose". **Do you ratify that wording, or hold the stronger claim pending v2 fixtures (mixed-class agents; an immortal condition that yields signal)?**

**Q3. What does "without trust" mean, and does the title change?** [KO]: honest-executor assumption "collides with phrases such as 'without trust' and 'the math is the accountability.'" *Defensible reading:* no trusted intermediary *for the arithmetic* — each org recomputes its own consumption. *Indefensible reading:* no trust in executors — the paper's own §9 says otherwise. *v1.0.1 state:* cross-org title amended to "…Without a Trusted Intermediary for the Arithmetic…"; §10 point 6 rewritten. **Ratify the new title, revert to the original with a footnote, or choose a third wording?**

**Q4. Is the v1 claim "scarcity" at all, or "irreversibility within an honest process"?** [KO]: *"Encryption does not create scarcity … It cannot be derived from ciphertext length alone."* His proposed remedy is an authority — ledger, signed state machine, secure hardware, consensus. *Two answers exist in your own corpus:* (a) the mimir-grammar settlement path (DAML μ reservation → settlement, `μreserved = μrefunded + μconsumed`) — his answer, in design, Experimental; (b) the cube-protocol reading that custody is environmental — copying buys nothing because meaning exists only if the environment cooperates (capture §5a, a reading of a downstream thesis, not established). **Which do you put to him — the ledger, the traversal-custody thesis, both, or neither in a v1.0.0 response?** And do you accept his formulation that this is "a missing uniqueness and settlement layer" rather than a flaw in the scheme?

**Q5. Ecological vocabulary — permanent or provisional?** [KO] rec #9: "Differential survival is not speciation; monotonic decline is not a boom; a tail average is not evidence of equilibrium." *For adopting permanently:* no births, so none of the three can be observed; the survival ranking flips between runs (alpha 12 % / beta 4 % in v1.0.1; 4 % / 8 % in v1.0.0; 0–8 % across seeds). *For provisional:* §12.1 already names reproduction as future work; the terms could return as hypotheses. *v1.0.1 state:* replaced throughout with "tail population", "monotonic decline", "niche-differential survival"; Gause not invoked. **Ratify, or keep the ecological terms as explicitly-labelled hypotheses?**

**Q6. Do you accept his decomposition?** [KO]: *"separating five different jobs that the current paper asks one equation to perform: accounting, scarcity, authorization, provenance, and physical conservation. Agentropy does the first one. A serious v2 could show how it composes with the other four."* *For:* the verification supports exactly this — every confirmed defect is the identity being asked to do one of the other four. *Against / nuance:* "physical conservation" was framed in the IoT paper as a mapping with a stated calibration gap, not as physics; and the Reader's Note's four separations (identity / agency / authority / witness) are your own decomposition, which cuts differently. **Do you adopt his five-job framing in the response, map it onto the four separations, or decline the framing?**

**Q7. Do you cite the post-v1 work at all in a response about v1.0.0?** [KO] asked for it "clearly attributed rather than being quietly folded in." *For:* his closing six-layer stack maps stage-for-stage onto a control surface decided 2026-07-24, a month before his review (§4.3 table); recs #2, #3, #4, #6, #7, #8, #9, #10 each have a decision record or contract. *Against:* every one of those artifacts is **Experimental, production not authorized, expiring 2026-10-24**, D2 narrowed not closed, G3-9 estimator absent, Vór not an independent witness; citing them risks exactly the overclaim the review is about. **Do you name the grammar, and if so with which of the constraints in §4.1 attached verbatim?**

**Q8. Do you offer the "immortal = copy-attack regime" reframing?** [CS finding, notes §2.3]: the proper control for "depletion" is *decrypt without destroy*, which is what a cloned agent gets; his double-spend finding and the ablation's IMMORTAL condition are the same experiment. *For:* it turns his strongest criticism into the ablation's clearest result. *Against:* it is the author's agent's synthesis, not in the paper, and could read as spin. **Offer it, or leave it for v2?**

**Q9. Result-changing fixes — ship the new reference numbers, or hold the paper at v1.0.0 numbers with errata only?** F2 moved token survival 45.5 % → 97.5 % and the rich/poor ratio 2.1× → 9.8×; F4 moved recycling 77.3 % → 29.3 %; F6 moved RANDOM stratification 1.9× → 3.1×. *v1.0.1 state:* tables show both columns, labelled. **Keep two-column tables, or revert the numbers and carry the changes only in `ERRATA-v1.0.1.md`?**

**Q10. Deposit timing.** A v1.0.1 Zenodo version would mint a version DOI under the concept DOI; the v1.0.0 DOI stays immutable and his review keeps pointing at it. **Deposit before he publishes so the response can cite it, after, or not at all until v2?**

**Q11. His closing three lines and your corollaries.** [KO]: *"The log is not the authorization. The hash is not the event. Encryption is not scarcity."* The Reader's Note (H2-FM2, 2026-07-30) lists as category errors "treating capability as permission … treating records as identity; treating signatures as truth" and states `Capability ⇏ Authority`. **Do you say that his conclusions and your published corollaries coincide — and if so, how, given the Note predates the review but he has not read it?**

**Q12. The one thing he asks that no fix answers: rec #8, "test competing causal explanations."** The repaired ablation shows the fixtures cannot separate structure from depletion for pure-class agents and that stratification is explained by data-mass alone. **Is the necessary-condition hypothesis one you want to keep exposing to that kind of test in v2, or does the CFO direction (`WHAT-WOULD-TEST-THE-THEORY.md`) replace simulation ablations as the test?**

---

## 4. Post-v1 work — clearly distinguished

Nothing in this section is in v1.0.0, and nothing in it rescues a v1.0.0 claim. Each entry carries the constraint under which it may be described. Dates are decision dates from the artifacts, not from memory.

### 4.0 Name the λ collision before anything else

The paper's `λ` and the grammar's `λ` are different quantities that share a letter:

| | Symbol | Definition | Source |
|---|---|---|---|
| Paper | `λ` | **decay / forgetting rate** in the stigmergic update `w_{t+1} = (1−λ)·w_t + α·r`; `λ ∈ [0,1]`; the closing line "`λ > 0`" means "decay is present" | `paper/agentropy.md` Appendix C |
| Grammar | `λₑ(t, h \| F) = Qq(Λₑ(t, h \| F))` | **risk-adjusted lower quantile of reachable useful work** `Λ`; `0 < q ≤ 0.10`; published with `lambda_lower / lambda_expected / lambda_upper` and `conditioning` | `mimir-grammar` `standard/agentropy-measurement-contract.md` §4 |

Any citation of the grammar in the response must state this first, or the reader will equate a decay rate with a capacity quantile.

### 4.1 Honesty constraints — verbatim, attach to every grammar citation

From `mimir-grammar/standard/README.md` and the decision records:

- **"Experimental — approved for controlled validation"**; **"Production use: Not authorized"**; **"Validation authorization expires: 2026-10-24 or completion of the protocol, whichever occurs first."**
- **D2** (an implementer can publish an optimistically biased λ): **"NARROWED, NOT CLOSED, never 'closed'"** (`agentropy-measurement-contract.md` §10 note; `v0.6.3-exp.2` §"D2 remains NARROWED, not closed").
- **G3-9** (fixtures, test vectors, reference estimator): **"Deferred, explicitly … none exist"** (`v0.6.3-exp.1` G3-9 row). No λ has been computed by a conforming estimator.
- **Vór**: designed, **not provisioned** as an independent operational root (RAV-1084 / SP2; ADR-023 accepted 2026-08-31 — R1 separation *authorized*, not complete; the accountability spine is switched off in production; anchors are on a public testnet, Base Sepolia).
- Public verification claim is **`inclusion_only`**; completeness is **`not_proven_v1`** (settlement adoption §3.6; accountability profile).

### 4.2 Repository state, corrected against the brief

The brief for this lane said mimir-grammar v0.7.0 was "on `main` as of 2026-09-04, PR #4." **That is not so.** `origin/main` = `d2c9c80` (PR #3, ADR-005), `VERSION` = `0.6.3-exp.2`, `release/status.json` = candidate-cutover-pending. v0.7.0 is branch `docs/rav-1583-mimir-grammar-v0-7-0` = `refs/pull/4/head` = `45b7d2a`, **open, not merged**; `origin/main` does not contain it. The v0.6.1-exp package (threat model, settlement contract, measurement contract, accountability profile, experimental protocol; decisions 2026-07-24, amended 2026-07-25, Gate 3 amendments 2026-07-28) *is* on `main`. Cite v0.6.1-exp / v0.6.3-exp.2 as the published lineage and v0.7.0 as an open PR.

### 4.3 [KO] six-layer stack ↔ [NW] v0.6.1 §3.5 control surface

Kurt's closing architecture (review, "What I Think Agentropy Actually Is", 2026-08-22) against the required command path in `standard/decisions/v0.6.1-agentropy-settlement-adoption.md` §3.5 (decision date 2026-07-24). The mapping is [CS]; the interpretation is Nate's.

| [KO] stack layer (2026-08-22) | [NW] §3.5 control-surface stage (2026-07-24) | Governing artifact | Constraint |
|---|---|---|---|
| signed authority | official SDK → Endpoint/Gateway → **Rig authentication → Forseti policy → Freyr Várar** | accountability integration profile; Várar = signed, TTL'd capability issued after policy | Experimental; Vór not independent |
| unique action or capability | **DAML μ reservation or harvest contract** — "typed contract IDs and exact parent-child lineage"; "Every action begins with a reservation and closes exactly once" | cipher-mass settlement contract §3, §4.1, §6 | Experimental; production not authorized |
| typed resource budget | authoritative **μ** balances per domain; `μreserved = μrefunded + μconsumed`; domain invariant §4.2 | cipher-mass settlement contract §4 | synthetic/test μ only (threat model §1) |
| atomic execution and settlement | **canonical Bifrost → independent MCP/executor → DAML μ settlement** | settlement contract §6–7; "DAML unavailable before execution → Do not dispatch" | Experimental |
| local receipt | **Bifrost receipt/outbox → Vor** (private canonical evidence, Merkle batches) | accountability profile; three-ledger boundary §3.6 | Vór designed, not provisioned; canonicalization is `rav-cjson-v1`, **not** RFC 8785 JCS (ruling 2026-09-03) |
| independent external commitment | **scheduled Ethereum commitment** | §3.6: Ethereum owns "public commitments", not completeness | `inclusion_only / not_proven_v1`; Base Sepolia testnet; anchor bounds alteration, not omission |

Kurt: *"Agentropy currently supplies pieces of the typed budget, local accounting, and receipt layers. It does not yet supply the authority, uniqueness, atomic settlement, or independent witness layers."* The table shows where each of the four missing layers is *specified*. It shows nothing about whether any is *built*; see 4.1.

### 4.4 The other post-v1 threads, each with its status

- **Vór / Týr** — Týr ratified as **judge** 2026-08-02 (ADR-008 accepted; runestack PR #38): Vór witnesses, Týr judges; verdicts are witnessed records with evidence chains, never opaque scalars; remedy debt is minted by judgment. Vór runtime-proven **not** an independent witness 2026-08-30 (same process as the issuer, holds its own ledger key, assigns its own `seq`); ADR-023 accepted 2026-08-31 with R1 (separate operational root), R2 (Base Sepolia with written expiry), R3 (issuance deeds into the anchored chain). *Bears on:* his "independent witness" layer and his five Merkle bullets — the estate's own finding was that an anchor "bounds alteration, not omission; only an independent sequencer fixes omission." Status: **specified and ruled; not built.**
- **Enacted vs attested** — session capture 2026-08-14 (`~/docs/60-research/research-and-development/Cypher Mass — Enacted Capability and the Attestation Boundary.md`): cypher mass [NW] as a depletable bearer capability where decryption is the spend; enacted-vs-attested [CS → NW-ratified] as the distinction between capacity-that-is-the-resource and a claim-about-capability; XMSS/LMS (RFC 8391/8554, SP 800-208) as the nearest primitive — stateful, finite, dead on exhaustion, budget minted not extended, and **does not solve custody**. Status: **candidate corollary that has not earned the name; no evidence status; mechanism altitude.** Its own §0e strikes the "dead agent" framing (depleted mass is exhausted capacity, not death) and §0f flags "agency is scalar IS λ" as an unearned amplification — carry both.
- **Bounded genesis** — ruling 2026-08-12: genesis is declared, not derived; bound it by custody (hardware root), not-before (public unpredictable beacon embedded in the deed), not-after (deed hash anchored where others witness it). Corrected 2026-08-16: **no hardware was purchased**; NetHSM deferred; lab runs a throwaway software dev root. *Bears on:* his "signed authority" layer — the estate's answer to "who signs the first authority" is a bounded declaration, which is also the honest answer to his observation that a namespace registry "introduces a trust anchor." Status: **ruled; $0 work only.**
- **Receipt canonicalization** — 2026-09-03 ruling: `rav-cjson-v1` (UTF-8 byte order), deliberately **not** RFC 8785 JCS (UTF-16 order); the two diverge on non-BMP characters. *Bears on:* his "local receipt" layer. Do not cite RFC 8785.

### 4.5 What must not be said

- That any of 4.3–4.4 is running, proven, or "answers" the review. It is where recs #2, #3, #4, #6, #7 are being *designed*.
- That the grammar's λ measures the paper's λ.
- That `μreserved = μrefunded + μconsumed` is the paper's equation in another notation without noting it is a *reservation* invariant over a settlement domain with an authority, exactly the layer he says v1 lacks.
- That the CFO direction (`WHAT-WOULD-TEST-THE-THEORY.md`) is evidence. It is a direction, attributed [CS], not ratified.

---

*Reproduction:* `bash docs/reviews/2026-08-22-overmier-v1.0.0/identity_proof.sh`, then the commands in `VERIFICATION-NOTES.md` §6. Kurt's harness path: `~/docs/30-projects/agentropy-poc/2026-08-21-agentropy-targeted-verification.py`.
