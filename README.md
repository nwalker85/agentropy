# Agentropy — Agent Mass Theory

**A conservation law for autonomous agents. One constraint. Four domains. Zero violations.**

> *An agent is a pattern of entropy management persisting autonomously.*

This repository contains the paper and the complete, runnable reference implementation for **Agent Mass Theory (AMT)** — a single conservation law for digital agents:

```
C_{n+1} + S_{n+1} + L_n = C_n
```

An agent's cipher mass after an interaction (`C_{n+1}`), plus the signal extracted (`S_{n+1}`), plus the loss incurred (`L_n`), equals its mass before (`C_n`). Nothing is created; nothing disappears. The law is not a protocol — it is an algebraic identity of AES-256-GCM decryption.

Applied **unmodified** across four unrelated domains — cross-organizational accountability, token economics, physical-IoT resource management, and population ecology — it produces dynamics that no participant programmed: independent per-organization auditability, market stratification, unified resource accounting, niche-differential survival and nutrient cycling. Across **750 agents and 5,415 interactions**, plus a **50,000-agent / ~2.3-million-visit scale test**, there are **zero conservation violations** — the equation is an accounting identity and cannot fail in a correct implementation. A systematic ablation study is consistent with structured, irreversible depletion being a *necessary condition* for these dynamics; with its controls repaired (v1.0.1) it establishes that depletion is necessary for every dynamic measured and that class-selective structure is necessary for per-class attribution.

## Paper

- **[`paper/agentropy.md`](paper/agentropy.md)** — *Agentropy: A Conservation Law as a Necessary Condition for Life-Like Dynamics.*
- Domain papers: [cross-org accountability](paper/cross_org_accountability.md) · [token economy](paper/token_economy.md) · [physical IoT](paper/physical_iot.md) · [population ecology](paper/marketplace.md).
- **[`paper/ERRATA-v1.0.1.md`](paper/ERRATA-v1.0.1.md)** — what v1.0.1 corrects, and why. The deposited v1.0.0 text is preserved at [DOI 10.5281/zenodo.20818597](https://doi.org/10.5281/zenodo.20818597).

## v1.0.1 (patch)

v1.0.1 responds to Kurt Overmier's open technical review of v1.0.0 (received 2026-08-22; verification record in [`docs/reviews/2026-08-22-overmier-v1.0.0/`](docs/reviews/2026-08-22-overmier-v1.0.0/)). It is a patch release: code fixes for confirmed bugs and wording corrections where the papers claimed more than the code does. No new architecture — uniqueness, settlement, signing and external anchoring are v2 work. The one-line version of the correction: **the equation is an accounting identity, and an accounting identity does not by itself give you scarcity, authorization, or non-repudiation.**

## Reproduce

```bash
pip install -r requirements-dev.txt   # cryptography (>=3.4.8) + pytest
python -m pytest                      # 31 tests, incl. known-limitations tests that pass while the limitation is present

python3 amt_cross_org_demo.py        # Domain 1: cross-org accountability
python3 amt_token_economy_demo.py    # Domain 2: token economy
python3 amt_physical_iot_demo.py     # Domain 3: physical IoT
python3 amt_marketplace_demo.py      # Domain 4: population ecology  (AMT_SEED=n to sample other runs)
python3 amt_ablation_demo.py         # Ablation study (paper §9)
python3 amt_scale.py --agents 50000 --steps 50   # population-scale verification
```

Every interaction asserts the conservation identity (`mass_before == mass_after + signal + loss`). A violation crashes the program. None has ever fired — because `loss` is defined as the remainder (paper Appendix B), which is also why zero violations is a statement about the bookkeeping, not about nature.

## Repository map

| File | Purpose |
|------|---------|
| `amt_core.py` | The conservation law: `Layer`, `Agent`, `Environment`, `interact()`, `AgentFactory` |
| `amt_extensions.py` | Ledgers (local/public), Merkle commitments, nodes, topology, behavior |
| `amt_cross_org.py` · `amt_token_economy.py` · `amt_physical_iot.py` · `amt_marketplace.py` | The four domain models (+ `*_demo.py` runners) |
| `amt_ablation.py` | CONTROL / IMMORTAL / RANDOM / RANDOM-MATCHED ablation (paper §9) |
| `amt_scale.py` | Population-scale verification |
| `tests/` | pytest suite: conservation identity, price enforcement, determinism, marketplace accounting, ablation controls, known limitations |
| `paper/` | The paper, the four domain papers, and `ERRATA-v1.0.1.md` |
| `docs/reviews/` | Verification record for the Overmier review of v1.0.0 |

## Citation

```
Walker, N. (2026). Agentropy: A Conservation Law as a Necessary Condition for
Life-Like Dynamics. https://github.com/nwalker85/agentropy
```

## License

Reference implementation (code): **MIT** (see `LICENSE`). Paper text (`paper/`): **CC BY 4.0**.

---

*`λ > 0`. The signal continues.*
