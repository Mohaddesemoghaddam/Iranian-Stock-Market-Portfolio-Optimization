# Iranian Stock Market Portfolio Optimization

### Benchmark-relative asset allocation with reproducible linear programming

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Pyomo](https://img.shields.io/badge/Optimization-Pyomo%20%2B%20GLPK-445566)](https://www.pyomo.org/) [![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)](#scope--limitations)

A research-focused, **long-only stock portfolio allocation** workflow built around four historical exercises with Iranian equity price matrices. It formulates a **benchmark-relative linear program**, visualizes fitted portfolio growth, and offers an optional **chronological holdout evaluation** to help distinguish historical fit from generalization.

> **Disclosure:** The four source Excel datasets are **not distributed** here, and the included CSV example is **synthetic**. The historical four optimizations were run in the uploaded original notebook; refactored code and holdout mode have not been rerun against the unavailable real workbooks. This repository does **not** claim live trading performance or future returns.

---

## At a glance

| Component | Design |
| --- | --- |
| **Domain** | Iranian equity price matrices and a market benchmark |
| **Method** | Linear programming (LP), solved with **Pyomo + GLPK** |
| **Portfolio** | Fully invested, long only: $w_i \ge 0$, $\sum_i w_i = 1$ |
| **Risk-style constraint** | Every **training** period: portfolio active return $\ge -k$ |
| **Original experiments** | Four historical worksheets (`Dataset1.xlsx`–`Dataset4.xlsx`) |
| **Evaluation** | Full-sample historical fit **and** chronological holdout (available when rerun) |
| **Outputs** | Portfolio weights, return series, wealth curves, summary CSVs |

## Why it matters

Rather than heuristically picking a stock or plotting prices, this project turns the allocation decision into an **explicit optimization problem**. It also documents a common methodological trap in quantitative research: **an optimal historical fit is not an independently tested investment strategy**.

## Optimization model

For $n$ assets over $T$ **fitting** periods, let $r_{i,t}$ be the price-based return of asset $i$, $b_t$ the benchmark return, $w_i$ its weight, and $k$ the permitted underperformance per period.

$$
\begin{aligned}
\max_{w}\quad & \frac{1}{T}\sum_{t=1}^{T}\left(\sum_{i=1}^{n}w_i r_{i,t}-b_t\right) \\
\text{subject to}\quad & \sum_{i=1}^{n} w_i = 1, \quad w_i \ge 0, \\
& \sum_{i=1}^{n}w_i r_{i,t}\ge b_t-k, \qquad \forall t\in\mathcal{T}_\mathrm{fit}.
\end{aligned}
$$

The original coursework used **$k = 0.02$**: a maximum historical **two-percentage-point** shortfall relative to the benchmark **in each fitted period**. It is **not** an absolute loss cap, a volatility bound, or an out-of-sample guarantee. Because benchmark returns are fixed, maximizing mean active return here is equivalent to maximizing the portfolio's historical mean return subject to the floor.

## Repository layout

```text
Iranian-Stock-Market-Portfolio-Optimization/
├── README.md
├── notebooks/
│   └── Iranian_Stock_Market_Portfolio_Optimization.ipynb
├── src/
│   └── portfolio_optimizer.py        # Excel contract, Pyomo LP, evaluation metrics
├── scripts/
│   ├── run_portfolio.py              # Noninteractive CLI for all datasets
│   ├── generate_synthetic_example.py
│   └── pre_publish_check.py
├── tests/
│   └── test_portfolio_optimizer.py
├── data/
│   ├── example/synthetic_price_matrix.csv   # DEMO ONLY
│   └── raw/README.md                        # Place your licensed Excel files here
├── docs/
│   ├── HISTORICAL_RESULTS.md
│   ├── historical_outputs.json
│   └── figures/                              # Original in-sample plots
├── requirements.txt
└── .github/workflows/ci.yml
```

## Installation

Requirements: **Python 3.10+**, `glpsol` executable (GLPK), and dependencies in `requirements.txt`.

**macOS (Homebrew)**

```bash
brew install glpk
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
which glpsol
```

**Ubuntu/Debian:** `sudo apt-get install -y glpk-utils` before installing Python dependencies. For Conda: `conda install -c conda-forge glpk`.

## Quick start — synthetic demo (no market data required)

```bash
python scripts/run_portfolio.py --files data/example/synthetic_price_matrix.csv --k 0.02
```

This generates local, ignored files in `results/`: weights, summary metrics, and wealth charts. The demo workbook contains **fictional prices generated with a fixed random seed**; nothing should be inferred about real Iranian equities from the demo output.

Alternatively, open [`notebooks/Iranian_Stock_Market_Portfolio_Optimization.ipynb`](notebooks/Iranian_Stock_Market_Portfolio_Optimization.ipynb) in VS Code or Jupyter and run cells from top to bottom. The notebook will **explicitly warn** if it uses synthetic data.

## Run with your own historical worksheets

Store licensed source files as:

```text
data/raw/Dataset1.xlsx
data/raw/Dataset2.xlsx
data/raw/Dataset3.xlsx
data/raw/Dataset4.xlsx
```

Then run:

```bash
python scripts/run_portfolio.py --files data/raw/Dataset1.xlsx data/raw/Dataset2.xlsx data/raw/Dataset3.xlsx data/raw/Dataset4.xlsx --k 0.02 --train-fraction 0.7
```

### Excel input contract

The loader implements the source notebook's **transpose-first** layout:

- **Rows:** one investable asset per row; **last row is the benchmark** (not tradable).
- **Columns:** consecutive observation periods, already ordered from oldest to newest.
- **Cells:** strictly positive instrument prices; no missing/non-numeric cells.
- **Names (optional):** a first **text-only** column with unique asset tickers and a benchmark name. Without it, stocks are labeled `Asset_01`, `Asset_02`, etc. We do **not** guess real stock names.
- **First Excel sheet:** selected by default; `--sheet` can specify a sheet name or 0-based index. The explicitly synthetic demo is CSV in the same row-oriented format.

Example (illustrative values only):

| Instrument | T001 | T002 | T003 | T004 |
| --- | ---: | ---: | ---: | ---: |
| SYNTH_01 | 100 | 101 | 100 | 103 |
| SYNTH_02 | 100 | 100 | 102 | 101 |
| SYNTH_BENCHMARK | 100 | 101 | 101 | 102 |

**Critical:** No sorting is performed. You must confirm that source columns reflect ascending time, and whether the prices are adjusted for splits/dividends. Calculating returns from unadjusted prices can seriously distort any portfolio analysis.

## Evaluation protocol & output interpretation

For each dataset the CLI writes three distinct analyses:

| Stage | Where weights are fitted | Where performance is calculated | Interpretation |
| --- | --- | --- | --- |
| `in_sample_full` | All observed periods | Same periods | **Historical optimum**, likely optimistic |
| `chronological_train` | First 70% of return periods | Same first 70% | Training-period fit |
| `chronological_test` | First 70% only | Remaining final 30% | **Holdout evaluation**, static weights |

For each stage: weights (`*_weights.csv`), periodic returns (`*_returns.csv`), a wealth curve (`*_wealth.png`), and aggregate `results/summary.csv`. All output files are generated **locally only** and ignored by Git.

Reported statistics are **per period and unannualized**, because the source does not establish a verified trading frequency. The test period can breach the fitted $-k$ floor; that does **not** mean the solver failed.

## Four original historical runs

In the uploaded coursework notebook, GLPK reported `OPTIMAL LP SOLUTION FOUND` for **each of four Excel workbooks**. The published images below are the **original in-sample plots**, *not newly recomputed performance*:

| Dataset1 | Dataset2 |
|:--:|:--:|
| ![Original Dataset1 in-sample](docs/figures/historical_in_sample_dataset_1.png) | ![Original Dataset2 in-sample](docs/figures/historical_in_sample_dataset_2.png) |
| Dataset3 | Dataset4 |
| ![Original Dataset3 in-sample](docs/figures/historical_in_sample_dataset_3.png) | ![Original Dataset4 in-sample](docs/figures/historical_in_sample_dataset_4.png) |

See [historical solver summaries and active weights](docs/HISTORICAL_RESULTS.md). The names/dates of real stocks and source provenance were not available for independent validation.

## Quality checks

```bash
python scripts/pre_publish_check.py
python -m pytest -q
```

CI runs notebook structure/syntax validation, loader and evaluation tests, and a synthetic-data Pyomo–GLPK solver test on Linux.

## Scope & limitations

- No causal or future-performance claims, and no implied endorsement of specific Iranian securities.
- Original Excel data and verified trade dates are missing; raw data are **never committed** by default.
- Static, long-only historical weights; transaction costs, market impact, liquidity, borrow costs, taxes and portfolio rebalancing are outside scope.
- A chronological split alone does not model realistic retraining or execution; a rolling-origin evaluation would be stronger.
- No guarantee that the LP remains feasible under a tighter $k$ or different market conditions.
- Before reusing plots in research, verify data rights, index conventions and adjustments.

**Purpose:** educational and research reproducibility, not investment advice.
