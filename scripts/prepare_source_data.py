#!/usr/bin/env python3
"""Generate source_data.h5 for the Qlib Factor R&D Loop.

Downloads CSI300 market data (OHLCV + VWAP) from Qlib and saves it
as an HDF5 file for use by factor.py during backtest rounds.

Prerequisites:
    - Qlib data must be downloaded first:
      cd Qlib-with-Claudex/scripts
      python get_data.py qlib_data --name qlib_data_simple \
        --target_dir ~/.qlib/qlib_data/cn_data --region cn

Usage:
    python scripts/prepare_source_data.py --output_dir .claude/artifacts/rdloop/my_run --rounds 5
    python scripts/prepare_source_data.py --output_dir /tmp/test_run --rounds 3

    # Quick test (single file, no round directories)
    python scripts/prepare_source_data.py --output /tmp/source_data.h5
"""
import multiprocessing
multiprocessing.set_start_method("fork", force=True)

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate source_data.h5 for the R&D loop")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output_dir", type=str,
                       help="Artifact directory. Creates round_N/implementations/source_data.h5 for each round.")
    group.add_argument("--output", type=str,
                       help="Single output file path (for quick testing)")
    parser.add_argument("--rounds", type=int, default=5,
                        help="Number of rounds to prepare (default: 5)")
    parser.add_argument("--n_instruments", type=int, default=50,
                        help="Number of instruments to include (default: 50)")
    parser.add_argument("--start_time", type=str, default="2019-01-01",
                        help="Start date (default: 2019-01-01)")
    parser.add_argument("--end_time", type=str, default="2020-12-31",
                        help="End date (default: 2020-12-31). Note: Simple data ends June 2021.")
    parser.add_argument("--provider_uri", type=str, default="~/.qlib/qlib_data/cn_data",
                        help="Qlib data directory")
    args = parser.parse_args()

    import qlib
    import pandas as pd
    from qlib.data import D

    qlib.init(provider_uri=args.provider_uri, region="cn")

    instruments = D.instruments("csi300")
    stock_list = D.list_instruments(instruments, start_time=args.start_time, end_time=args.end_time)
    symbols = sorted(stock_list.keys())[:args.n_instruments]

    print(f"Fetching data for {len(symbols)} instruments ({args.start_time} to {args.end_time})...")
    df = D.features(
        symbols,
        ["$open", "$close", "$high", "$low", "$volume", "$vwap"],
        start_time=args.start_time,
        end_time=args.end_time,
    )
    df.columns = ["open", "close", "high", "low", "volume", "vwap"]

    print(f"Data shape: {df.shape}")
    print(f"Index levels: {df.index.names}")
    print(f"Columns: {list(df.columns)}")
    for col in df.columns:
        pct = df[col].notna().mean() * 100
        print(f"  {col}: {pct:.1f}% non-null")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_hdf(str(output_path), key="data")
        print(f"\nSaved: {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
    else:
        artifact_dir = Path(args.output_dir)
        for r in range(args.rounds):
            impl_dir = artifact_dir / f"round_{r}" / "implementations"
            impl_dir.mkdir(parents=True, exist_ok=True)
            output_path = impl_dir / "source_data.h5"
            df.to_hdf(str(output_path), key="data")
            print(f"Saved: {output_path}")
        print(f"\nPrepared {args.rounds} rounds in {artifact_dir}")


if __name__ == "__main__":
    main()
