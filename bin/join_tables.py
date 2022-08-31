#!/usr/bin/env python
"""Join cami output and kaiju, kraken2 or centrifuge output by taxid."""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd


logger = logging.getLogger()


# Keep track of what are the names of columns for taxid:s
TAXID_COLS: dict = {
    "kaiju": "taxon_id",
    "kraken2": "taxid",
    "centrifuge": "taxID",
    "cami": "cami_taxid",
}

TABLE_DATA_TYPES: dict = {
    "kaiju": {
        "line_number": int,
        "file": str,
        "percent": float,
        "reads_count": int,
        "taxon_id": str,
        "taxon_name": str,
        "RPM": float,
    },
    "kraken2": {
        "line_number": int,
        "percentage_fragments_covered": float,
        "num_fragments_covered": int,
        "reads_count": int,
        "rank_code": str,
        "taxid": str,
        "sci_name": str,
        "RPM": float,
    },
    "centrifuge": {
        "line_number": int,
        "name": str,
        "taxID": str,
        "taxRank": str,
        "genomeSize": int,
        "numReads": int,
        "reads_count": int,
        "abundance": float,
        "RPM": float,
    },
    "cami": {
        "@@TAXID": str,
        "RANK": str,
        "TAXPATH": str,
        "TAXPATHSN": str,
        "PERCENTAGE": float,
    },
}


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Join cami output and kaiju, kraken2 or centrifuge output by taxid",
        epilog="Example: python join_tables.py SRR12875570_pe-SRR12875570-centrifuge.cami-profile.tsv SRR12875570_pe-SRR12875570-centrifuge.report.filtered.tsv",
    )
    parser.add_argument(
        "cami_table",
        metavar="CAMI_TABLE",
        type=Path,
        help="Tsv file cami table",
    )
    parser.add_argument(
        "classifier_table",
        metavar="CLASSIFIER_TABLE",
        type=Path,
        help="Filtered tsv file from, e.g. centrifuge, kaiju or kraken2",
    )
    parser.add_argument(
        "-o",
        "--output-file-name",
        metavar="Path",
        type=Path,
        default=Path("joined.tsv"),
        help="The output tsv file name for the joined table",
    )
    parser.add_argument(
        "-c",
        "--classifier-name",
        help="The type of classifier which filtered output we wish to join to its cami output",
        choices=("kaiju", "kraken2", "centrifuge"),
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )
    return parser.parse_args(argv)


def read_classifier_output(tsv: Path, classifier_name: str) -> pd.DataFrame:
    """Read into DataFrame a classifier tsv file

    Args:
        tsv (Path): Path to the classifier tsv file
        classifier_name (str): Name of the classifier, e.g. kaiju

    Returns:
        pd.DataFrame: The tsv table converted into a DataFrame
    """
    data_types: dict = TABLE_DATA_TYPES.get(classifier_name)
    logger.info("Reading %s tsv file into a DataFrame", classifier_name)
    return pd.read_table(tsv, index_col=0, dtype=data_types)


def read_cami_output(tsv: Path) -> pd.DataFrame:
    """Read cami profile output tsv file into a DataFrame

    Args:
        tsv (Path): Path to the cami profile file

    Returns:
        pd.DataFrame: Cami profile table converted into a DataFrame
    """
    data_types: dict = TABLE_DATA_TYPES.get("cami")
    logger.info("Reading cami profile into a pandas DataFrame")
    df: pd.DataFrame = pd.read_table(tsv, skiprows=4, dtype=data_types)
    # Get rid of '@@' in '@@TAXID'
    col_name_mappings: dict = {
        "@@TAXID": "cami_taxid",
        "RANK": "cami_rank",
        "TAXPATH": "cami_taxpath",
        "TAXPATHSN": "cami_taxpathsn",
        "PERCENTAGE": "cami_percentage",
    }
    logger.info("Removing leading '@@' in '@@TAXID'")
    df.rename(columns=col_name_mappings, errors="raise", inplace=True)
    return df


def join_dfs(
    classifier_df: pd.DataFrame, cami_df: pd.DataFrame, classifier_name: str
) -> pd.DataFrame:
    """Join cami profile DataFrame and its corresponding classifier DataFrame

    Args:
        classifier_df (pd.DataFrame): Classifier DataFrame
        cami_df (pd.DataFrame): Cami profile DataFrame
        classifier_name (str): Name of the classifier of which the DataFrame is

    Returns:
        pd.DataFrame: Merged DataFrame ('left join') where classifier DataFrame is the left one
    """
    logger.info(
        "Left joining %s DataFrame with %s as key and cami profile using %s as key",
        classifier_name,
        TAXID_COLS.get(classifier_name),
    ), TAXID_COLS.get("cami")
    return classifier_df.merge(
        cami_df,
        how="left",
        left_on=TAXID_COLS.get(classifier_name),
        right_on=TAXID_COLS.get("cami"),
    )


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")

    cami_file: Path = args.cami_table
    if not cami_file.is_file():
        logger.error("The given input file %s was not found!", cami_file)
        sys.exit(1)
    cami_df = read_cami_output(cami_file)
    classifier_file: Path = args.classifier_table
    if not classifier_file.is_file():
        logger.error("The given input file %s was not found!", classifier_file)
        sys.exit(2)
    classifier_name: str = args.classifier_name
    classifier_df = read_classifier_output(classifier_file, classifier_name)
    merged_df = join_dfs(classifier_df, cami_df, classifier_name)
    out_tsv_file: Path = args.output_file_name
    logger.info(
        "Storing joined %s and cami profile df into a tsv file: %s",
        classifier_name,
        out_tsv_file,
    )
    merged_df.to_csv(out_tsv_file, sep="\t", index=False)


if __name__ == "__main__":
    sys.exit(main())
