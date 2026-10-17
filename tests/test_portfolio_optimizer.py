from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
from portfolio_optimizer import load_legacy_excel, chronological_split, evaluate_fixed_weights, performance_summary, solve_linear_portfolio
from generate_synthetic_example import generate_example


def test_transpose_benchmark_last_and_prices(tmp_path):
    path=generate_example(tmp_path/'demo.csv',periods=30,assets=4)
    ds=load_legacy_excel(path)
    assert ds.prices.shape==(30,5)
    assert ds.asset_columns==[f'SYNTH_{i:02d}' for i in range(1,5)]
    assert ds.prices.columns[-1]=='Market_Benchmark'
    assert len(ds.returns)==29
    assert ds.returns.notna().all().all()


def test_split_is_chronological_without_overlap(tmp_path):
    ds=load_legacy_excel(generate_example(tmp_path/'demo.csv',periods=40))
    train,test=chronological_split(ds.returns,.7)
    assert len(train)+len(test)==len(ds.returns)
    assert set(train.index).isdisjoint(test.index)
    assert train.index[-1]==ds.returns.index[len(train)-1]
    assert test.index[0]==ds.returns.index[len(train)]


def test_reject_bad_prices(tmp_path):
    p=tmp_path/'bad.csv'
    pd.DataFrame({'t1':[2.,4.],'t2':[3.,0.],'t3':[4.,5.],'t4':[5.,6.]}).to_csv(p,index=False)
    with pytest.raises(ValueError,match='strictly positive'):
        load_legacy_excel(p)


def test_eval_and_drawdown_math():
    a=pd.DataFrame({'Asset_01':[.10,-.10], 'Market_Benchmark':[0.,0.]})
    report=evaluate_fixed_weights(a,pd.Series({'Asset_01':1.}))
    assert np.allclose(report.Portfolio_Wealth,[1.1,.99])
    result=performance_summary(report,k=.02)
    assert result['active_floor_breach_count']==1
    assert np.isclose(result['portfolio_max_drawdown'],-.10)
    assert np.isclose(result['portfolio_total_return'],-.01)


def test_optimizer_optimal_and_training_floor(tmp_path):
    pytest.importorskip('pyomo')
    import pyomo.environ as pe
    if not pe.SolverFactory('glpk').available(exception_flag=False):
        pytest.skip('GLPK not installed')
    ds=load_legacy_excel(generate_example(tmp_path/'demo.csv',periods=40,assets=4))
    tr,te=chronological_split(ds.returns,.7)
    weights=solve_linear_portfolio(tr,k=.02)
    assert np.isclose(weights.sum(),1,atol=1e-7)
    assert (weights>=0).all()
    train_report=evaluate_fixed_weights(tr,weights)
    assert train_report.Active_Return.min()>=-.020001
    _=evaluate_fixed_weights(te,weights)  # same weights, no leakage
