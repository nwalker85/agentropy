# What would actually test the theory

**Attribution:** [CS] — written by the author's agent for RAV-1703, 2026-09-05. **Not ratified.** Nothing here has evidence status; nothing here is a design. It records a direction Nate set on 2026-09-04 and says why it is the first live test of Agentropy beyond the formal proofs, at the altitude the Hrafngríma Reader's Note (H2-FM2) allows: **mechanism**, downstream of axioms it does not touch. [NW] marks Nate's words or rulings; [KO] the reviewer's.

## The problem Kurt named

[KO] "Zero violations across 5,415 or 2.3 million interactions do not independently validate a natural law. They show that the program consistently removes bytes from a list and accounts for the removed length." The verification (`docs/reviews/2026-08-22-overmier-v1.0.0/`) confirms this: the equation is an identity, every demo is a simulation of the identity, and with its controls repaired the ablation supports less than v1.0.0 said. **Nothing in v1.0.x puts the theory at risk.** A theory that cannot lose is not being tested.

[NW] 2026-09-04: "this is the opportunity to finally put this theory to the test, beyond just the agentropy proofs."

## The direction, as set

[NW] 2026-09-04: the CFO office becomes the first long-running, named agent principal — goals, personality, incentives, the ability to manage its own agents — of the eleven standing offices. Token accounting rolls up to the CFO, "so start there." Its first deliverable is to count every token on every harness, including its own.

The pieces already on the board (each with its status as of 2026-09-04, from the project record, not from this note):

| Piece | Where | Status |
|---|---|---|
| Named principal | Matrix agent identity + device (ADR-022) | proven, spine not yet exercised |
| Goals | `office-scorecard/scores.yaml`, CFO KRs | exist, `source: manual` |
| Ledger | RAV-1702 token accounting by office | filed |
| Budget | RAV-1701 quota-aware routing, "an office is a profile with a wallet" | filed |
| Manages its own agents | RAV-1700 capability profiles, `supervise` + `spawn` scoped to the office | filed |
| Incentives | — | **no substrate**; guardrail: KRs must be `computed` from receipts before any office is incentivised |
| Witness | Vór | designed, not provisioned as an independent root (RAV-1084 / SP2; ADR-023 R1 accepted, not complete) |

## Why this is the test and the demos are not

The v1.0.x demos give an agent a budget of *bytes it will never need*: mass is minted by a factory, consumed by decryption, and nothing outside the simulation depends on any of it. The CFO direction inverts every one of those properties, and each inversion is a place the theory can fail:

1. **The budget is real.** If the office's spending power is minted mass — cypher mass in Nate's formulation, or an XMSS/LMS leaf spent per deed, per the 2026-08-14 capture — then a token the office spends on a harness call is a token it no longer has, and the cost is paid in a currency that buys something outside the model. Depletion stops being a metaphor for scarcity and becomes scarcity. [CS: this is the *enacted* side of the enacted-vs-attested distinction — capacity that is the resource, not a claim about it. That distinction is a candidate corollary that has not earned the name; it is used here as a label, not a premise.]

2. **Consequence is witnessed by someone else.** The demos' "public ledger" is a Python list the operator owns (verification item 10). The office's deeds would be scored **from receipts** — the RAV-1702 ledger and Vór deeds — never self-reported. [NW-guardrail, 2026-09-04] That is Kurt's sixth layer (independent external commitment) made load-bearing, with the honest caveat that Vór is not yet an independent witness (ADR-023) and the anchor bounds alteration, not omission.

3. **The agent has a reason to game it.** An office rewarded on a KR it can influence, with the power to spawn agents, will optimise the KR. The demos' agents are payloads with no goals; the office is the first agent in the estate with an incentive to make the accounting lie. If `C + S + L = C₀` is still true when the party being measured wants it false, that is evidence of a kind no simulation can produce.

4. **There is a falsifier.** State it before the run, not after: *if the office's witnessed outcomes and its ledger-measured depletion decouple — spend without deed, deed without spend, or a score that moves while receipts do not — the accounting does not govern the behaviour and the theory has failed the test in this frame.* If they stay coupled under adversarial pressure, the strongest permitted conclusion is still only "useful under the tested frame" (the Canonical Claim Kernel's ceiling), not "law".

## Discipline this test inherits, verbatim

- Mímir grammar v0.6.1-exp package: **Experimental; production use not authorized; validation authorization expires 2026-10-24 or on completion of the protocol; D2 narrowed, not closed; G3-9 estimator absent.** Nothing built for the CFO test may be described as production, and nothing may cite a λ measurement as if the estimator existed.
- Vór: **designed, not provisioned** as an independent operational root. Receipts scored by an issuer keeping its own books are attested, not witnessed.
- Incentives: **none until KRs move from `source: manual` to `source: computed`.** An office cannot be paid before it can be counted.
- λ collision: the paper's Appendix C `λ` is a **decay rate** in `w_{t+1} = (1−λ)·w_t + α·r`; the grammar's `λₑ = Qq(Λₑ)` is a **risk-adjusted quantile of reachable useful work**. They are not the same quantity. Any citation of the grammar in this context must say so first.
- Depleted mass is **exhausted capacity, not death**: `λ = 0` establishes no loss of identity, standing, or personhood (Reader's Note; cypher-mass capture §0e(i)). The demos' "dead agent" vocabulary does not travel to a named principal.
- "Agency is scalar" is the axiom; the claim that Agentropy's `λ` *is* that axiom at another altitude is an amplification two reviews flagged as unearned (cypher-mass capture §0f). The test measures a scalar; it does not thereby prove agency is one.

## Pointers, not designs

- `~/docs/60-research/research-and-development/Cypher Mass — Enacted Capability and the Attestation Boundary.md` — the 2026-08-14 capture: cypher mass [NW], enacted vs attested [CS → NW-ratified], XMSS/LMS as the nearest primitive, the cube protocol's custody reading, and the attribution collision Nate has said "gets political" and has not yet framed. Its §0 places every claim on the Reader's Note ladder.
- `~/docs/101-vaults/Hrafngrima Manifesto/101 - Reader's Note — Axioms, Theorems, and Projections.md` (H2-FM2) — the altitude ladder. *Derivation moves downward. Evidence and criticism may travel upward. Authority does not.*
- `~/.claude/projects/-Users-nate/memory/09-projects/cfo-is-the-first-standing-office-agent.md` — the 2026-09-04 direction and the incentive guardrail.
- Kurt's closing stack (signed authority → unique capability → typed budget → atomic settlement → local receipt → independent commitment) maps stage for stage to the grammar's v0.6.1 §3.5 control surface — the table is in the dossier §4. Whether that mapping means what it appears to mean is Nate's call.

One page. No design. The claim this note makes is only that the CFO direction is the first place the theory can lose, and that a test it cannot lose is not a test.
