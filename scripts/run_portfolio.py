"""Run one or more historical Excel datasets from the command line."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / 'src'))
from portfolio_optimizer import (load_legacy_excel, chronological_split,
 solve_linear_portfolio, evaluate_fixed_weights, performance_summary)


def save_plot(report: pd.DataFrame, path: Path, label: str) -> None:
    fig,ax=plt.subplots(figsize=(9,4.5))
    ax.plot(report.index.astype(str), report.Portfolio_Wealth, label="Portfolio")
    ax.plot(report.index.astype(str), report.Benchmark_Wealth, label="Benchmark")
    # Dense monthly/daily periods -> show only sparse ticks.
    step=max(1,len(report)//9)
    ax.set_xticks(list(range(0,len(report),step)))
    ax.set_xticklabels([str(report.index[x]) for x in range(0,len(report),step)],rotation=25,ha='right')
    ax.set_title(label);ax.set_ylabel("Growth of 1 unit");ax.legend();ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(path,dpi=160);plt.close(fig)


def main() -> int:
    p=argparse.ArgumentParser(description="Portfolio LP research (historical, not investment advice)")
    p.add_argument('--files',type=Path,nargs='+',required=True,help='Original-style Excel price matrices')
    p.add_argument('--output-dir',type=Path,default=ROOT/'results')
    p.add_argument('--k',type=float,default=.02,help='Per-period return shortfall allowance (0.02 = 2 percentage points)')
    p.add_argument('--train-fraction',type=float,default=.7)
    p.add_argument('--sheet',default='0',help='Excel sheet index (0-based) or sheet name')
    args=p.parse_args()
    if not (0.0 <= args.k < 1): p.error('--k must be in [0,1)')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    sheet=int(args.sheet) if args.sheet.isdecimal() else args.sheet
    result_rows=[]
    for filepath in args.files:
        ds=load_legacy_excel(filepath,sheet_name=sheet)
        dataset_out=args.output_dir/ds.name
        dataset_out.mkdir(parents=True,exist_ok=True)
        observed=ds.returns
        print(f"[{ds.name}] periods={len(observed)} assets={len(ds.asset_columns)}")
        split_train, split_test=chronological_split(observed,args.train_fraction)
        scenarios={'in_sample_full':(observed,observed),
                   'chronological_train':(split_train,split_train),
                   'chronological_test':(split_train,split_test)}
        full_weights=None; split_weights=None
        for stage,(fitting,evaluation) in scenarios.items():
            if stage=='in_sample_full':
                full_weights=solve_linear_portfolio(fitting,k=args.k)
                weights=full_weights
            else:
                if split_weights is None: split_weights=solve_linear_portfolio(split_train,k=args.k)
                weights=split_weights
            comparison=evaluate_fixed_weights(evaluation,weights)
            summary=performance_summary(comparison,k=args.k)
            comparison.to_csv(dataset_out/f'{stage}_returns.csv',index_label='period')
            weights.to_csv(dataset_out/f'{stage}_weights.csv',header=['weight'])
            save_plot(comparison,dataset_out/f'{stage}_wealth.png',f'{ds.name} • {stage.replace("_"," ")}')
            result_rows.append(dict(dataset=ds.name,stage=stage,**summary))
            print(' ',stage,summary)
    frame=pd.DataFrame(result_rows)
    frame.to_csv(args.output_dir/'summary.csv',index=False)
    (args.output_dir/'run_config.json').write_text(json.dumps({'files':[str(x) for x in args.files],
         'k':args.k,'train_fraction':args.train_fraction,'sheet':str(args.sheet),
         'caveat':'No transaction costs, no lookahead in chronological_test, benchmark historical only'},indent=2))
    print(f"Saved local outputs to {args.output_dir}")
    return 0

if __name__=='__main__':
    raise SystemExit(main())
