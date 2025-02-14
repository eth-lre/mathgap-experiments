# MathGAP: Out-of-Distribution Evaluation on Problems with Arbitrarily Complex Proofs

## Generating Datasets
### Setup
While in repo-folder:
```
cd experiments/opedal24_ood_eval
python3 -m venv .venv
. .venv/bin/activate
cd ../..
pip install -e .
cd experiments/opedal24_ood_eval
```

Example (when in /experiments/opedal24_ood_eval):
```
python generate.py linear-comparison -o "out/depth.csv" -n 30 --min-depth 1 --max-depth 4
```

### Cite as:
```bibtex
@inproceedings{opedal2025mathgap,
title={Math{GAP}: Out-of-Distribution Evaluation on Problems with Arbitrarily Complex Proofs},
author={Andreas Opedal and Haruki Shirakami and Bernhard Sch{\"o}lkopf and Abulhair Saparov and Mrinmaya Sachan},
booktitle={The Thirteenth International Conference on Learning Representations},
year={2025},
url={https://openreview.net/forum?id=5ck9PIrTpH}
}