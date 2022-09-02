#!/usr/bin/env python
"""Calculate RPM values for each called taxon."""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd


logger = logging.getLogger()


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate RPM values for each called taxon in a given classifier output file",
        epilog="Example: python rpm_filter.py SRR12875558_se-SRR12875558-kaiju.txt -n 2",
    )
    parser.add_argument(
        "classifier_output_file",
        metavar="CLASSIFIER_OUTPUT_FILE",
        type=Path,
        help="The tsv file from, e.g. centrifuge, kaiju or kraken2",
    )
    parser.add_argument(
        "-o",
        "--rpm-filtered-output-file",
        metavar="Path",
        type=Path,
        help="The output tsv file which has been filtered by user given rpm value",
    )
    parser.add_argument(
        "-n",
        "--reads-column-number",
        metavar="int",
        help="The 0-based column number where the supporting reads count is",
        type=int,
    )
    parser.add_argument(
        "-c",
        "--column-names",
        metavar="str",
        help="New column names to give for the table",
        type=str,
    )
    parser.add_argument(
        "-s",
        "--string-colname",
        metavar="str",
        help="Name of a column that must be read as string, e.g 'taxon_id' in kaiju output",
        type=str,
    )
    parser.add_argument(
        "-r",
        "--rpm-filtering-threshold",
        metavar="float",
        help="The RPM value by which to filter the given table",
        type=float,
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )
    return parser.parse_args(argv)


def read_classifier_output_file(tsv: Path, str_column_name: str = "") -> pd.DataFrame:
    """Read classifier output file into a DataFrame

    Args:
        tsv (Path): Classifier output file path

    Returns:
        pd.DataFrame: Classifier output file as a DataFrame
    """
    if str_column_name:
        return pd.read_table(tsv, index_col=False, dtype={str_column_name: str})
    return pd.read_table(tsv, index_col=False)


def prepare_df(
    df: pd.DataFrame,
    reads_col_index: int,
    col_names: list[str] = [],
    reads_col_name: str = "reads_count",
) -> pd.DataFrame:
    """Convert a given column's data type and column name

    Args:
        df (pd.DataFrame): Dataframe where the column type and column name are changed
        reads_col_index (int): 0-based index of where the column changes should be applied
        col_names (list[str]): List of column names for the table
        reads_col_name (str, optional): A name to give for the reads column. Defaults to "reads_count".

    Returns:
        pd.DataFrame: A table with reads column name cast to int and having known column names
    """
    # Convert column data types to int so that sum can be calculated
    df.iloc[:, reads_col_index] = df.iloc[:, reads_col_index].astype(int)
    # Assign new column names if the user has given them otherwise go with the already
    # existing ones except rename the reads column
    if col_names:
        df.columns = col_names
    else:
        df.columns.values[reads_col_index] = reads_col_name
    return df


def get_sum_of_column(df: pd.DataFrame, column_to_get_sum_of: int) -> int:
    """Get the sum of a given column

    Args:
        df (pd.DataFramem): DataFrame where the column is
        column_to_get_sum_of (int): The 0-based index of the column to get_sum of

    Returns:
        int: The sum of the column
    """
    col_sum: int = df.iloc[:, column_to_get_sum_of].sum()
    logger.info("The sum of the given column is: %s", str(col_sum))
    return col_sum


def add_rpm_column(
    df: pd.DataFrame, col_sum_per_million: int, col_name: str = "reads_count"
) -> pd.DataFrame:
    """Add Reads per million column to given data frame

    Args:
        df (pd.DataFrame): Pandas DataFrame where the RPM column is to be added
        col_sum_per_million (int): Sum of all reads divided by million
        col_name (str, optional): Column name where the reads counts assigned to taxons are. Defaults to "reads_count".

    Returns:
        pd.DataFrame: DataFrame where the RPM column is added
    """
    df["RPM"] = df.apply(lambda row: row[col_name] * col_sum_per_million, axis=1)
    df["RPM"] = df.apply(lambda row: round(row["RPM"], 1), axis=1)
    return df


def filter_by_rpm(df: pd.DataFrame, rpm_value: float) -> pd.DataFrame:
    """Filter rows where the RPM value is higher than the given value

    Args:
        df (pd.DataFrame): The DataFrame where to filter by given RPM value
        rpm_value (float): The threshold RPM value to use for filtering

    Returns:
        pd.DataFrame: The DataFrame where the RPM filtering has been applied
    """
    return df[df["RPM"] >= rpm_value]


def post_process_df(df: pd.DataFrame, index_name: str = "line_number") -> pd.DataFrame:
    """Drop old index and give the new index a name

    Args:
        df (pd.DataFrame): DataFrame where the post processing is to be done
        index_name (str, optional): The new name for the index. Defaults to "line_number".

    Returns:
        pd.DataFrame: Transformed DataFrame where index is updated
    """
    df = df.reset_index(drop=True)
    df.index.name = index_name
    return df


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")
    classifier_file: Path = args.classifier_output_file
    if not classifier_file.is_file():
        logger.error("The given input file %s was not found!", classifier_file)
        sys.exit(1)
    # Should some column name be read as string?
    if args.string_colname:
        df: pd.DataFrame = read_classifier_output_file(
            classifier_file, args.string_colname
        )
    else:
        df: pd.DataFrame = read_classifier_output_file(classifier_file)
    reads_col_index: int = args.reads_column_number
    col_names: str = args.column_names
    if col_names:
        cols: list = col_names.split(",")
        df_prepared: pd.DataFrame = prepare_df(df, reads_col_index, cols)
    else:
        df_prepared: pd.DataFrame = prepare_df(df, reads_col_index)
    col_sum: int = get_sum_of_column(df_prepared, reads_col_index)
    col_sum_per_million: float = col_sum / 1000000
    df_rpm_added: pd.DataFrame = add_rpm_column(df_prepared, col_sum_per_million)
    df_rpm_filtered: pd.DataFrame = filter_by_rpm(
        df_rpm_added, args.rpm_filtering_threshold
    )
    df = post_process_df(df_rpm_filtered)
    output_fname: Path = args.rpm_filtered_output_file
    if output_fname:
        df.to_csv(output_fname, sep="\t")
    else:
        default_name = (
            f"{str(classifier_file.parent)}/{str(classifier_file.stem)}.filtered.tsv"
        )
        df.to_csv(default_name, sep="\t")


if __name__ == "__main__":
    sys.exit(main())
