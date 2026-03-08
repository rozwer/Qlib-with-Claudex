#!/usr/bin/env python3
"""Calculate IC/IR/RankIC metrics from a factor backtest result.

Reads result.h5 (factor values) and source_data.h5 (market data),
computes daily IC, IR, and Rank IC, then saves run_result.json.

Usage:
    python scripts/calc_ic.py <workspace> <artifact_dir> <round_idx> <factor_name>

Example:
    python scripts/calc_ic.py \
      .claude/artifacts/rdloop/my_run/round_0/implementations \
      .claude/artifacts/rdloop/my_run \
      0 \
      momentum_5d
"""
import multiprocessing
multiprocessing.set_start_method("fork", force=True)

import json
import sys

import numpy as np
import pandas as pd


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <workspace> <artifact_dir> <round_idx> <factor_name>")
        sys.exit(1)

    workspace, artifact_dir = sys.argv[1], sys.argv[2]
    round_idx, factor_name = int(sys.argv[3]), sys.argv[4]

    result = pd.read_hdf(f"{workspace}/result.h5")
    source = pd.read_hdf(f"{workspace}/source_data.h5")

    # Index-order independent: reset_index + merge approach
    result_df = result.reset_index()
    source_df = source.reset_index()

    factor_col = [c for c in result_df.columns if c not in ("instrument", "datetime")][0]
    result_df = result_df.rename(columns={factor_col: "factor"})

    source_df = source_df.sort_values(["instrument", "datetime"])
    source_df["forward_return"] = source_df.groupby("instrument")["close"].transform(
        lambda s: s.pct_change().shift(-1)
    )

    merged = pd.merge(
        result_df[["instrument", "datetime", "factor"]],
        source_df[["instrument", "datetime", "forward_return"]],
        on=["instrument", "datetime"],
    )
    merged = merged.dropna(subset=["factor", "forward_return"])

    # Daily IC / Rank IC (use loop to avoid groupby.apply return type issues)
    ic_list, rank_ic_list = [], []
    for dt, grp in merged.groupby("datetime"):
        if len(grp) < 5:
            continue
        ic_list.append(grp["factor"].corr(grp["forward_return"]))
        rank_ic_list.append(grp["factor"].rank().corr(grp["forward_return"].rank()))

    daily_ic = pd.Series(ic_list).dropna()
    daily_rank_ic = pd.Series(rank_ic_list).dropna()

    run_result = {
        "status": "success",
        "factor_name": factor_name,
        "metrics": {
            "ic_mean": round(float(daily_ic.mean()), 6),
            "ic_std": round(float(daily_ic.std()), 6),
            "ir": round(float(daily_ic.mean() / daily_ic.std()), 6) if daily_ic.std() > 0 else 0.0,
            "rank_ic_mean": round(float(daily_rank_ic.mean()), 6),
            "daily_ic_positive_ratio": round(float((daily_ic > 0).mean()), 4),
            "n_observations": int(merged.shape[0]),
            "n_days": int(len(daily_ic)),
        },
    }

    output_path = f"{artifact_dir}/round_{round_idx}/run_result.json"
    with open(output_path, "w") as f:
        json.dump(run_result, f, indent=2)

    # Print summary
    m = run_result["metrics"]
    print(f"Factor: {factor_name}")
    print(f"IC={m['ic_mean']:.4f}  IR={m['ir']:.4f}  RankIC={m['rank_ic_mean']:.4f}  IC>0={m['daily_ic_positive_ratio']:.1%}")
    print(f"Observations: {m['n_observations']:,}  Days: {m['n_days']}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
