import os
from pathlib import Path

import click
import pandas as pd

from datasets import *

def save_df_to_csv(df: pd.DataFrame, file_path: str):
    path = Path(file_path)
    folder_name = path.parent.name
    if not path.parent.exists():
        os.makedirs(folder_name, exist_ok=True)
    df.to_csv(file_path, index=False)

@click.group()
def cli():
    pass

@cli.command()
@click.option("-o", "--out-path", required=True, help="Where the generated dataset will be stored")
@click.option("-n", "--nr-problems", default=50, help="The number of problems that should be generated")
@click.option("--min-depth", default=1, help="The min depth of the trees that will be generated")
@click.option("--max-depth", default=3, help="The max depth of the trees that will be generated")
@click.option("-s", "--seed", default=140499, help="The seed to be used")
def linear_comparison(out_path: str, nr_problems: int, min_depth: int, max_depth: int, seed: int):
    path = os.path.join("experiments/opedal24_ood_eval/data") if 'mathgap' in os.listdir() else os.path.join("data")
    df = pd.DataFrame(generate_linear_comparison(nr_problems=nr_problems, min_depth=min_depth, max_depth=max_depth, seed=seed, data_folder=path))
    save_df_to_csv(df, out_path)

@cli.command()
@click.option("-o", "--out-path", required=True, help="Where the generated dataset will be stored")
@click.option("-n", "--nr-problems", default=50, help="The number of problems that should be generated")
@click.option("--min-depth", default=1, help="The min depth of the trees that will be generated")
@click.option("--max-depth", default=3, help="The max depth of the trees that will be generated")
@click.option("-s", "--seed", default=140499, help="The seed to be used")
def linear_transfer(out_path: str, nr_problems: int, min_depth: int, max_depth: int, seed: int):
    path = os.path.join("experiments/opedal24_ood_eval/data") if 'mathgap' in os.listdir() else os.path.join("data")
    df = pd.DataFrame(generate_linear_transfer(nr_problems=nr_problems, min_depth=min_depth, max_depth=max_depth, seed=seed, data_folder=path))
    save_df_to_csv(df, out_path)

@cli.command()
@click.option("-o", "--out-path", required=True, help="Where the generated dataset will be stored")
@click.option("-n", "--nr-problems", default=50, help="The number of problems that should be generated")
@click.option("--min-width", default=2, help="The min width of the trees that will be generated")
@click.option("--max-width", default=4, help="The max width of the trees that will be generated")
@click.option("-s", "--seed", default=140499, help="The seed to be used")
def linear_partwhole(out_path: str, nr_problems: int, min_width: int, max_width: int, seed: int):
    path = os.path.join("experiments/opedal24_ood_eval/data") if 'mathgap' in os.listdir() else os.path.join("data")
    df = pd.DataFrame(generate_linear_partwhole(nr_problems=nr_problems, min_width=min_width, max_width=max_width, seed=seed, data_folder=path))
    save_df_to_csv(df, out_path)

@cli.command()
@click.option("-o", "--out-path", required=True, help="Where the generated dataset will be stored")
@click.option("-n", "--nr-problems", default=50, help="The number of problems that should be generated")
@click.option("--depth", default=1, help="The depth of the trees that will be generated")
@click.option("--move-idx", default=1, help="The depth of the trees that will be generated")
@click.option("-s", "--seed", default=140499, help="The seed to be used")
def moved_linear_comparison(out_path: str, nr_problems: int, depth: int, move_idx: int, seed: int):
    path = os.path.join("experiments/opedal24_ood_eval/data") if 'mathgap' in os.listdir() else os.path.join("data")
    df = pd.DataFrame(generate_moved_linear_comparison(nr_problems=nr_problems, depth=depth, move_idx=move_idx, seed=seed, data_folder=path))
    save_df_to_csv(df, out_path)

@cli.command()
@click.option("-o", "--out-path", required=True, help="Where the generated dataset will be stored")
@click.option("-n", "--nr-problems", default=50, help="The number of problems that should be generated")
@click.option("--min-depth", default=1, help="The min depth of the trees that will be generated")
@click.option("--max-depth", default=3, help="The max depth of the trees that will be generated")
@click.option("-s", "--seed", default=140499, help="The seed to be used")
def nonlinear_comparison(out_path: str, nr_problems: int, min_depth: int, max_depth: int, seed: int):
    path = os.path.join("experiments/opedal24_ood_eval/data") if 'mathgap' in os.listdir() else os.path.join("data")
    df = pd.DataFrame(generate_nonlinear_comparison(nr_problems=nr_problems, min_depth=min_depth, max_depth=max_depth, seed=seed, data_folder=path))
    save_df_to_csv(df, out_path)

if __name__ == "__main__":
    cli()