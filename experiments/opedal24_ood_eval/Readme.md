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

**Note:** it may take some time to find valid numerical instantiations for deep problems (depth >= 5), leading to long runtimes. The function will abort generation after a fixed number of failed instantiations, yielding the following message:
> Failed to find a valid instantiation after 100000 iterations!

This can be mitigated by setting ``leaf_max_value`` in ``datasets.py`` to a larger value.
