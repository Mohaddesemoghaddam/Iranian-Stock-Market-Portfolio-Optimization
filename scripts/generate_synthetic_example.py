"""Create explicitly synthetic sample prices for a runnable tutorial/demo.

This data is NOT real Tehran Stock Exchange / Iran stock market data.
"""
from pathlib import Path
import csv
import numpy as np


def generate_example(path: str | Path, *, seed: int = 42, periods: int = 120, assets: int = 8) -> Path:
    if assets < 2 or periods < 10: raise ValueError("assets>=2 and periods>=10 are required")
    rng = np.random.default_rng(seed)
    common = rng.normal(0.0006, 0.006, size=periods - 1)
    # A shared market movement with small idiosyncratic noise, chosen for a
    # simple feasible k=0.02 demonstration; never mistaken for real data.
    stock_returns = common[:, None] + rng.normal(0, 0.003, size=(periods - 1, assets))
    bench_returns = common + rng.normal(0, 0.0015, size=periods - 1)
    series = np.vstack([np.ones(assets+1)*1000,
                        1000*np.cumprod(1 + np.column_stack([stock_returns, bench_returns]),axis=0)])
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow(['Instrument']+[f'T{t:03d}' for t in range(1,periods+1)])
        for i,row in enumerate(series.T):
            name=f'SYNTH_{i+1:02d}' if i<assets else 'SYNTH_BENCHMARK'
            writer.writerow([name]+[float(v) for v in row])
    return path


if __name__ == "__main__":
    here=Path(__file__).resolve().parents[1]
    path=generate_example(here/'data/example/synthetic_price_matrix.csv')
    print(f"Synthetic demo only: {path}")
