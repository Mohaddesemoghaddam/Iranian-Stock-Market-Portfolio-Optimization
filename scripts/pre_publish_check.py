"""Static publication checks; no claim of real-data execution."""
from pathlib import Path
import json
import ast
import nbformat
ROOT=Path(__file__).resolve().parents[1]
paths=[ROOT/'README.md',ROOT/'requirements.txt',ROOT/'notebooks/Iranian_Stock_Market_Portfolio_Optimization.ipynb',ROOT/'data/example/synthetic_price_matrix.csv',ROOT/'src/portfolio_optimizer.py',ROOT/'scripts/run_portfolio.py',ROOT/'docs/HISTORICAL_RESULTS.md']
missing=[str(p.relative_to(ROOT)) for p in paths if not p.exists()]
if missing: raise SystemExit(f'MISSING FILES: {missing}')
nb=nbformat.read(paths[2],as_version=4)
nbformat.validate(nb)
for i,c in enumerate(nb.cells):
    if c.cell_type=='code':
        ast.parse(c.source,filename=f'notebook-cell-{i}')
    if 'google.colab' in c.source or 'files.upload' in c.source:
        raise SystemExit(f'Colab-dependent cell {i}')
for filename in ['src/portfolio_optimizer.py','scripts/run_portfolio.py','scripts/generate_synthetic_example.py']:
    ast.parse((ROOT/filename).read_text(encoding='utf-8'),filename=filename)
historical=json.loads((ROOT/'docs/historical_outputs.json').read_text(encoding='utf-8'))
assert len(historical)==4 and all(h['solver_reported_optimal'] for h in historical)
print('PASS: expected files, notebook format, code syntax, four original historical solver flags')
print('STATIC ONLY: this does not re-run original Iranian market data.')
