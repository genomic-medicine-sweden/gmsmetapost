#!/usr/bin/env python
"""Concatenate kaiju-cami, kraken2-cami and centrifuge-cami tsv tables into one file"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd


logger = logging.getLogger()

RENAMING_MAPPINGS: dict = {
    "centrifuge": {
        "name": "taxon_name",
        "taxID": "taxid",
        "taxRank": "taxonomic_rank",
        "genomeSize": "centrifuge_genome_size",
        "numReads": "centrifuge_num_reads",
        "abundance": "centrifuge_abundance",
        "RPM": "rpm",
    },
    "kaiju": {
        "percent": "kaiju_percent",
        "taxon_id": "taxid",
        "RPM": "rpm",
    },
    "kraken2": {
        "percentage_fragments_covered": "kraken2_percentage_fragments_covered",
        "num_fragments_covered": "kraken2_num_fragments_covered",
        "sci_name": "taxon_name",
        "rank_code": "taxonomic_rank",
        "RPM": "rpm",
    },
}

DATA_TYPES: dict = {
    "centrifuge": {
        "name": str,
        "taxID": str,
        "taxRank": str,
        "genomeSize": int,
        "numReads": int,
        "reads_count": int,
        "abundance": float,
        "RPM": float,
        "cami_taxid": str,
        "cami_rank": str,
        "cami_taxpath": str,
        "cami_taxpathsn": str,
        "cami_percentage": float,
    },
    "kaiju": {
        "file": str,
        "percent": float,
        "reads_count": int,
        "taxon_id": str,
        "taxon_name": str,
        "RPM": float,
        "cami_taxid": str,
        "cami_rank": str,
        "cami_taxpath": str,
        "cami_taxpathsn": str,
        "cami_percentage": float,
    },
    "kraken2": {
        "percentage_fragments_covered": float,
        "num_fragments_covered": int,
        "reads_count": int,
        "rank_code": str,
        "taxid": str,
        "sci_name": str,
        "RPM": float,
        "cami_taxid": str,
        "cami_rank": str,
        "cami_taxpath": str,
        "cami_taxpathsn": str,
        "cami_percentage": float,
    },
}


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Concatenate kaiju-cami, kraken2-cami and centrifuge-cami tsv tables into one file",
        epilog="Example: python concat_tables.py -j kaiju.tsv -k kraken2.tsv -c centrifuge.tsv -o SRR12875570_pe-SRR12875570.tsv",
    )
    parser.add_argument(
        "-j",
        "--kaiju-file",
        metavar="kaiju-file",
        type=Path,
        help="Tsv file with kaiju table combined with cami table",
    )
    parser.add_argument(
        "-k",
        "--kraken2-file",
        metavar="kraken2-file",
        type=Path,
        help="Tsv file with kraken2 table combined with cami table",
    )
    parser.add_argument(
        "-c",
        "--centrifuge-file",
        metavar="centrifuge-file",
        type=Path,
        help="Tsv file with kraken2 table combined with cami table",
    )
    parser.add_argument(
        "-o",
        "--output-file-name",
        metavar="Path",
        type=Path,
        default=Path("concatenated.tsv"),
        help="The output tsv file name for the concatenated table",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )
    return parser.parse_args(argv)


def read_classifier(classifier: tuple[Path, str]) -> tuple[pd.DataFrame, str]:
    """Read classifier tsv into a DataFrame

    Args:
        classifier (tuple[Path, str]): Tuple with Path to classifier tsv and name of the classifier

    Returns:
        pd.DataFrame: DataFrame with classifier data
    """
    classifier_name: str = classifier[1]
    data_types: dict = DATA_TYPES.get(classifier_name)
    logger.info("Reading %s tsv file into a DataFrame", classifier_name)
    return (
        pd.read_table(classifier[0], index_col=False, dtype=data_types),
        classifier_name,
    )


def process_df(classifier: tuple[pd.DataFrame, str]) -> pd.DataFrame:
    """Rename DataFrame columns, add classifier name column and drop 'file' column from kaiju df

    Args:
        classifier (tuple[pd.DataFrame, str]): Tuple with classifier DataFrame and name of the classifier

    Returns:
        pd.DataFrame: Processed DataFrame with classifier data
    """
    classifier_df: pd.DataFrame = classifier[0]
    classifier_name: str = classifier[1]
    classifier_df.rename(columns=RENAMING_MAPPINGS.get(classifier_name), inplace=True)
    logger.info("Renaming %s DataFrame columns", classifier_name)
    classifier_df["classifier"] = classifier_name
    logger.info("Adding classifier name '%s' to DataFrame", classifier_name)
    # Remove non-informative 'file' column from kaiju df
    if classifier_name == "kaiju":
        classifier_df.drop("file", axis=1, inplace=True)
        logger.info("Dropping kaiju 'file' column")
    return classifier_df


def concatenate_dfs(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(dfs, ignore_index=True)


def check_if_exists(path_to_test: Path) -> Path:
    """Check if given input file exists

    Args:
        path_to_test (Path): Path which we want to check if it is a file

    Returns:
        Path: A valid file path
    """
    if not path_to_test.is_file():
        logger.error("The given input file %s was not found!", path_to_test)
        sys.exit(1)
    return path_to_test


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")

    kaiju_file: Path = check_if_exists(args.kaiju_file)
    kraken2_file: Path = check_if_exists(args.kraken2_file)
    centrifuge_file: Path = check_if_exists(args.centrifuge_file)

    concatenated_df: pd.DataFrame = concatenate_dfs(
        [
            process_df(read_classifier(data))
            for data in [
                (kaiju_file, "kaiju"),
                (kraken2_file, "kraken2"),
                (centrifuge_file, "centrifuge"),
            ]
        ]
    )
    # Sort rows by rpm and taxid values
    concatenated_df.sort_values(
        by=["rpm", "taxid"], ascending=[False, True], inplace=True
    )
    # Rearrange the columns
    concatenated_df = concatenated_df[
        [
            "taxon_name",
            "rpm",
            "taxid",
            "taxonomic_rank",
            "classifier",
            "centrifuge_genome_size",
            "centrifuge_num_reads",
            "centrifuge_abundance",
            "kaiju_percent",
            "kraken2_percentage_fragments_covered",
            "kraken2_num_fragments_covered",
            "reads_count",
            "cami_taxid",
            "cami_rank",
            "cami_taxpath",
            "cami_taxpathsn",
            "cami_percentage",
        ]
    ]
    concatenated_df.to_csv(args.output_file_name, sep="\t", index=False)


if __name__ == "__main__":
    sys.exit(main())
