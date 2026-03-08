#!/usr/bin/env python3
"""Check data quality of source_data.h5 and output data_quality.json.

Inspects missing rates per column and determines which columns are
usable (>50% non-null). This information is passed to the Planner
subagent to avoid generating hypotheses that rely on unusable columns.

Usage:
    python scripts/check_data_quality.py <source_data_path> <output_path>

Example:
    python scripts/check_data_quality.py \
      .claude/artifacts/rdloop/my_run/round_0/implementations/source_data.h5 \
      .claude/artifacts/rdloop/my_run/data_quality.json
"""
import multiprocessing
multiprocessing.set_start_method("fork", force=True)

import json
import sys

import pandas as pd


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source_data_path> <output_path>")
        sys.exit(1)

    source_path, output_path = sys.argv[1], sys.argv[2]

    df = pd.read_hdf(source_path, key="data")

    quality = {
        "total_rows": len(df),
        "columns": {},
    }

    for col in df.columns:
        notna = int(df[col].notna().sum())
        missing_pct = round((1 - notna / len(df)) * 100, 1)
        usable = notna > len(df) * 0.5
        quality["columns"][col] = {
            "notna": notna,
            "missing_pct": missing_pct,
            "usable": usable,
        }

    quality["usable_columns"] = [c for c, v in quality["columns"].items() if v["usable"]]

    with open(output_path, "w") as f:
        json.dump(quality, f, indent=2)

    # Print summary
    print(f"Total rows: {quality['total_rows']:,}")
    print(f"Columns:")
    for col, info in quality["columns"].items():
        status = "OK" if info["usable"] else "UNUSABLE"
        print(f"  {col}: {info['missing_pct']}% missing [{status}]")
    print(f"\nUsable columns: {quality['usable_columns']}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
