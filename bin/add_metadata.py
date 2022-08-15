#!/usr/bin/env python
"""Augment input tsv table with pairing and sample name data"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd

logger = logging.getLogger()


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Augment input tsv table with pairing and sample name data",
        epilog="Example: python add_meta.py SRR12875558_se-SRR12875558.tsv SRR12875558_se-SRR12875558.meta-added.tsv -p single_end -s SRR12875558_se-SRR12875558",
    )
    parser.add_argument(
        "input_file",
        metavar="INPUT-FILE",
        type=Path,
        help="Input file which to augment with metadata",
    )
    parser.add_argument(
        "output_file",
        metavar="OUTPUT-FILE",
        type=Path,
        help="Output tsv file name",
    )
    parser.add_argument(
        "-p",
        "--pairing",
        metavar="PAIRING",
        type=str,
        choices=("single_end", "paired_end"),
        help="Was the sample single end or paired end?",
    )
    parser.add_argument(
        "-s",
        "--sample-name",
        metavar="SAMPLE_NAME",
        type=str,
        help="Name of the sample",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="ERROR",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")

    input_file: Path = args.input_file
    if not input_file.is_file():
        logger.error("The given input file %s was not found!", input_file)
        sys.exit(1)

    df = pd.read_table(input_file, index_col=False)
    df["pairing"] = args.pairing
    df["sample_name"] = args.sample_name
    df.to_csv(args.output_file, index=False, sep="\t")


if __name__ == "__main__":
    sys.exit(main())
