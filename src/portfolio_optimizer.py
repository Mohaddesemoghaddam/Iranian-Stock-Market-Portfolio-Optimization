"""Reproducible historical portfolio experiments (not investment advice).

The legacy Excel layout has one instrument per *row* and chronological prices
across *columns*. The final instrument row is the market benchmark. Dataset
names, index composition and adjustment status are not inferred.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PriceDataset:
    name: str
    prices: pd.DataFrame  # chronological rows; stocks then market column
    benchmark_column: str = "Market_Benchmark"

    @property
    def returns(self) -> pd.DataFrame:
        result = self.prices.pct_change(fill_method=None).iloc[1:]
        if not np.isfinite(result.to_numpy(dtype=float)).all():
            raise ValueError("Returns include NaN/Inf. Check input prices.")
        return result

    @property
    def asset_columns(self) -> list[str]:
        return [col for col in self.prices.columns if col != self.benchmark_column]


def load_legacy_excel(path: str | Path, sheet_name: str | int = 0) -> PriceDataset:
    """Load original coursework format: instruments in rows; periods in columns.

    Last row must be the benchmark, and previous rows must be investable stocks.
    Optional first column of distinct *text* identifiers becomes instrument names.
    Original column order is trusted as chronological; it is never sorted.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing Excel file: {path}")
    if path.suffix.lower() == ".csv":
        raw = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        raw = pd.read_excel(path, sheet_name=sheet_name)
    else:
        raise ValueError("Expected .csv, .xlsx, .xlsm or .xls input file.")
    raw = raw.dropna(axis=0, how="all").dropna(axis=1, how="all")
    if raw.shape[0] < 2 or raw.shape[1] < 4:
        raise ValueError("Expected >=2 instrument rows (assets + market) and >=4 periods.")

    names: list[str] | None = None
    first = raw.iloc[:, 0]
    if first.map(lambda x: isinstance(x, str)).all() and pd.to_numeric(first, errors="coerce").isna().all():
        names = [str(x).strip() for x in first]
        raw = raw.iloc[:, 1:]
    elif pd.to_numeric(first, errors="coerce").isna().any():
        raise ValueError("The first column is partially nonnumeric; fix mixed price/label values.")

    if raw.shape[1] < 4:
        raise ValueError("Need >=4 chronological price observations.")
    numeric = raw.apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        positions = np.argwhere(numeric.isna().to_numpy())[:5].tolist()
        raise ValueError(f"Missing/nonnumeric price cells at [row, period] positions {positions}.")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all() or (numeric <= 0).any().any():
        raise ValueError("Prices must be finite and strictly positive; adjust/clean the source.")

    assets = [f"Asset_{i+1:02d}" for i in range(len(numeric)-1)] if names is None else names[:-1]
    if len(set(assets)) != len(assets) or "Market_Benchmark" in assets:
        raise ValueError("Asset identifiers must be unique and differ from Market_Benchmark.")
    columns = assets + ["Market_Benchmark"]
    prices = numeric.T.copy()
    prices.columns = columns
    # Retain source column order, including period labels, as-is.
    return PriceDataset(name=path.stem, prices=prices.astype(float))


def chronological_split(returns: pd.DataFrame, train_fraction: float = 0.7) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not (0.1 < train_fraction < 0.9):
        raise ValueError("train_fraction must be strictly between 0.1 and 0.9.")
    if len(returns) < 5:
        raise ValueError("At least 5 return periods are required for a chronological split.")
    cut = int(len(returns) * train_fraction)
    return returns.iloc[:cut].copy(), returns.iloc[cut:].copy()


def solve_linear_portfolio(returns: pd.DataFrame, *, benchmark_column: str = "Market_Benchmark",
                           k: float = 0.02, solver_name: str = "glpk") -> pd.Series:
    """Maximize historical mean active return under period-wise active floors.

    x_i >= 0, sum_i x_i = 1
    for each training period t: sum_i x_i * r[t,i] >= benchmark[t] - k.
    No test observation participates in fitting weights.
    """
    if not np.isfinite(k) or k < 0:
        raise ValueError("k must be a nonnegative finite per-period return difference.")
    if benchmark_column not in returns.columns:
        raise ValueError(f"Missing benchmark column: {benchmark_column}")
    assets = [c for c in returns.columns if c != benchmark_column]
    if not assets:
        raise ValueError("No investable assets detected.")
    if returns.empty or not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError("Return matrix must be nonempty and finite.")
    try:
        from pyomo.environ import (ConcreteModel, RangeSet, Var, NonNegativeReals, Objective,
                                   Constraint, maximize, SolverFactory, value, TerminationCondition)
    except ImportError as exc:
        raise RuntimeError("Pyomo is missing. Install requirements.txt first.") from exc

    instrument_returns = returns[assets].to_numpy(dtype=float)
    benchmark = returns[benchmark_column].to_numpy(dtype=float)
    t_count, n_assets = instrument_returns.shape
    m = ConcreteModel()
    m.assets = RangeSet(0, n_assets - 1)
    m.periods = RangeSet(0, t_count - 1)
    m.weight = Var(m.assets, domain=NonNegativeReals)
    m.budget = Constraint(expr=sum(m.weight[i] for i in m.assets) == 1.0)
    m.floor = Constraint(m.periods, rule=lambda model, t:
        sum(instrument_returns[t, i] * model.weight[i] for i in model.assets) >= benchmark[t] - k)
    m.objective = Objective(expr=sum(
        sum(instrument_returns[t, i] * m.weight[i] for i in m.assets) - benchmark[t]
        for t in m.periods) / t_count, sense=maximize)
    solver = SolverFactory(solver_name)
    if solver is None or not solver.available(exception_flag=False):
        raise RuntimeError(f"Solver '{solver_name}' not found. Install GLPK ('glpsol') on PATH.")
    result = solver.solve(m, tee=False)
    if result.solver.termination_condition != TerminationCondition.optimal:
        raise RuntimeError(f"LP did not reach optimal solution: {result.solver.termination_condition}. "
                           "The per-period floor might be infeasible for this k.")
    w = pd.Series([float(value(m.weight[i])) for i in m.assets], index=assets, name="weight")
    if abs(float(w.sum()) - 1.0) > 1e-6 or (w < -1e-7).any():
        raise RuntimeError("Solver returned weights violating the investment constraints.")
    w = w.clip(lower=0)
    w = w / w.sum()
    # Verify historical return floor (allow solver numerical tolerance).
    active = returns[assets].to_numpy() @ w.to_numpy() - benchmark
    if float(active.min()) < -k - 1e-6:
        raise RuntimeError("Solver returned weights violating the historical active-return floor.")
    return w


def evaluate_fixed_weights(returns: pd.DataFrame, weights: pd.Series, *,
                           benchmark_column: str = "Market_Benchmark") -> pd.DataFrame:
    """Hold portfolio weights constant (no rebalance / costs / slippage)."""
    missing = set(weights.index) - set(returns.columns)
    if missing: raise ValueError(f"Missing assets in evaluation data: {sorted(missing)}")
    p = (returns.reindex(columns=weights.index).to_numpy(dtype=float) @ weights.to_numpy(dtype=float))
    b = returns[benchmark_column].to_numpy(dtype=float)
    out = pd.DataFrame({"Portfolio_Return": p, "Benchmark_Return": b}, index=returns.index)
    out["Active_Return"] = out.Portfolio_Return - out.Benchmark_Return
    out["Portfolio_Wealth"] = (1 + out.Portfolio_Return).cumprod()
    out["Benchmark_Wealth"] = (1 + out.Benchmark_Return).cumprod()
    return out


def performance_summary(comparison: pd.DataFrame, *, k: float) -> dict[str, float | int]:
    """Unannualized realized historical statistics, unless period data are specified."""
    p = comparison.Portfolio_Return.to_numpy(dtype=float)
    b = comparison.Benchmark_Return.to_numpy(dtype=float)
    active = p - b
    wealth = (1 + p).cumprod()
    max_dd = float(np.min(wealth / np.maximum.accumulate(np.r_[1.0, wealth])[1:] - 1.0))
    return {
        "periods": int(len(p)),
        "portfolio_total_return": float(np.prod(1 + p) - 1),
        "benchmark_total_return": float(np.prod(1 + b) - 1),
        "mean_active_return_per_period": float(active.mean()),
        "worst_active_return_per_period": float(active.min()),
        "active_floor_breach_count": int(np.sum(active < -k - 1e-8)),
        "portfolio_volatility_per_period": float(np.std(p, ddof=1)) if len(p) > 1 else float("nan"),
        "portfolio_max_drawdown": max_dd,
    }
