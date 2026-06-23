# Agentropy — Agent Mass Theory

**A conservation law for autonomous agents. One constraint. Four domains. Zero violations.**

> *An agent is a pattern of entropy management persisting autonomously.*

This repository contains the paper and the complete, runnable reference implementation for **Agent Mass Theory (AMT)** — a single conservation law for digital agents:

```
C_{n+1} + S_{n+1} + L_n = C_n
```

An agent's cipher mass after an interaction (`C_{n+1}`), plus the signal extracted (`S_{n+1}`), plus the loss incurred (`L_n`), equals its mass before (`C_n`). Nothing is created; nothing disappears. The law is not a protocol — it is an algebraic identity of AES-256-GCM decryption.

Applied **unmodified** across four unrelated domains — cross-organizational accountability, token economics, physical-IoT resource management, and population ecology — it produces life-like dynamics (trustless auditability, market stratification, load-shedding, carrying capacity, speciation) that no participant programmed. Across **750 agents and 5,415 interactions**, plus a **50,000-agent / multi-million-interaction scale test**, there are **zero conservation violations**. A systematic ablation study establishes that structured, irreversible depletion is a *necessary condition* for these dynamics.

## Paper

- **[`paper/agentropy.md`](paper/agentropy.md)** — *Agentropy: A Conservation Law as a Necessary Condition for Life-Like Dynamics.*
- Domain papers: [cross-org accountability](paper/cross_org_accountability.md) · [token economy](paper/token_economy.md) · [physical IoT](paper/physical_iot.md) · [population ecology](paper/marketplace.md).

## Reproduce

```bash
pip install cryptography

python3 amt_cross_org_demo.py        # Domain 1: cross-org accountability
python3 amt_token_economy_demo.py    # Domain 2: token economy
python3 amt_physical_iot_demo.py     # Domain 3: physical IoT
python3 amt_marketplace_demo.py      # Domain 4: population ecology
python3 amt_ablation_demo.py         # Ablation study (paper §9)
python3 amt_scale.py --agents 50000 --steps 50   # population-scale verification
```

Every interaction asserts the conservation law (`mass_before == mass_after + signal + loss`). A violation crashes the program. None has ever fired.

## Repository map

| File | Purpose |
|------|---------|
| `amt_core.py` | The conservation law: `Layer`, `Agent`, `Environment`, `interact()`, `AgentFactory` |
| `amt_extensions.py` | Ledgers (local/public), Merkle commitments, nodes, topology, behavior |
| `amt_cross_org.py` · `amt_token_economy.py` · `amt_physical_iot.py` · `amt_marketplace.py` | The four domain models (+ `*_demo.py` runners) |
| `amt_ablation.py` | CONTROL / IMMORTAL / RANDOM ablation (paper §9) |
| `amt_scale.py` | Population-scale verification |
| `paper/` | The paper and the four domain papers |

## Citation

```
Walker, N. (2026). Agentropy: A Conservation Law as a Necessary Condition for
Life-Like Dynamics. https://github.com/nwalker85/agentropy
```

## License

Reference implementation (code): **MIT** (see `LICENSE`). Paper text (`paper/`): **CC BY 4.0**.

---

*`λ > 0`. The signal continues.*
