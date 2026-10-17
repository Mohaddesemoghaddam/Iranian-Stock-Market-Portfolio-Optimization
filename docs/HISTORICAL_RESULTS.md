# Original notebook: archived in-sample observations

These are **historical outputs from the user's original four repeated Colab experiments**, not results rerun by this repository. In the original workflow, the same price history was used to fit the allocation weights and display cumulative returns. Consequently, these are **in-sample backtests**, not evidence of out-of-sample performance or future investability. Underlying Excel datasets were not supplied with the notebook; named stock symbols, trading dates, index composition, and adjusted-price status cannot be independently verified.

All four GLPK solver logs contained `OPTIMAL LP SOLUTION FOUND`. The original code used `k=0.02` per observation, with long-only budget-constrained portfolio weights. Numeric identifiers 0–9 refer to original Excel row positions rather than verified listed symbols.

| Original source | GLPK status | Solver objective (mean active return per period) | Visual |
| --- | --- | ---: | --- |
| Dataset1.xlsx | Optimal | 0.00193275 | [Historical in-sample plot](figures/historical_in_sample_dataset_1.png) |
| Dataset2.xlsx | Optimal | 0.00176201 | [Historical in-sample plot](figures/historical_in_sample_dataset_2.png) |
| Dataset3.xlsx | Optimal | 0.00212378 | [Historical in-sample plot](figures/historical_in_sample_dataset_3.png) |
| Dataset4.xlsx | Optimal | 0.00207893 | [Historical in-sample plot](figures/historical_in_sample_dataset_4.png) |

For the originally printed active weights, inspect [`historical_outputs.json`](historical_outputs.json).

**Important:** Historical figure captions and bars have not been regenerated or adjusted. Their labels are as saved in the original notebook. The refactored canonical notebook has deliberately cleared execution outputs because it has not been rerun against the missing original Excel data. All new split-based results are computed only after a user supplies data and reruns the notebook.
