# Release notes

## Initial public research release

- Refactored four duplicated Google Colab sections into one canonical notebook and reusable Python functions.
- Removed environment-specific file upload/install cells and Persian coursework comments.
- Retained the exact conceptual LP objective/constraints (Pyomo + GLPK, `k=0.02`).
- Introduced an optional chronological 70/30 holdout analysis while marking historical four runs as in-sample.
- Retained historical output figures and solver/status/printed weights separately, without forging any refactored result.
- Added a labeled synthetic example, input validation, reports, CLI, unit tests, and GitHub Actions.
- Original Excel datasets were not included; updated notebook not rerun on source data.
