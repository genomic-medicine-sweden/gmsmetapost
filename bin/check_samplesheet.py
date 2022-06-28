#!/usr/bin/env python
"""Provide a command line tool to validate tabular samplesheets."""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger()


class RowChecker:
    """
    Define a service that can validate and transform each given row.

    Attributes:
        modified (list): A list of dicts, where each dict corresponds to a previously
            validated and transformed row. The order of rows is maintained.

    """

    VALID_FORMATS = (".tsv", )

    def __init__(
        self,
        sample_col: str = "sample",
        first_col: str = "kraken2",
        second_col: str = "centrifuge",
        **kwargs,
    ) -> None:
        """
        Initialize the row checker with the expected column names.

        Args:
            sample_col (str): The name of the column that contains the sample name
                (default "sample").
            first_col (str): The name of the column that contains the kraken2
                output tsv file path (default "kraken2").
            second_col (str): The name of the column that contains centrifuge
                output tsv file path (default "centrifuge").

        """
        super().__init__(**kwargs)
        self._sample_col: str = sample_col
        self._first_col: str = first_col
        self._second_col: str = second_col
        self._seen: set = set()
        self.modified: List[dict] = []

    def validate(self, row: dict) -> None:
        """
        Perform all validations on the given row and insert the read pairing status.

        Args:
            row (dict): A mapping from column headers (keys) to elements of that row
                (values).

        """
        self._validate_sample(row)
        self._validate_first(row)
        self._validate_second(row)
        self._seen.add((row[self._sample_col], row[self._first_col],
                        row[self._second_col]))
        self.modified.append(row)

    def _validate_sample(self, row: dict) -> None:
        """Assert that the sample name exists and convert spaces to underscores."""
        assert len(row[self._sample_col]) > 0, "Sample input is required."
        # Sanitize samples slightly.
        row[self._sample_col] = row[self._sample_col].replace(" ", "_")

    def _validate_first(self, row: dict) -> None:
        """Assert that the first tsv entry is non-empty and has the right format."""
        assert len(
            row[self._first_col]) > 0, "The kraken2 tsv file is required."
        self._validate_tsv_format(row[self._first_col])
        #self._validate_tsv_file_exists(row[self._first_col])

    def _validate_second(self, row: dict) -> None:
        """Assert that the second tsv entry has the right format if it exists."""
        assert len(
            row[self._second_col]) > 0, "The centrifuge tsv file is required."
        self._validate_tsv_format(row[self._second_col])
        #self._validate_tsv_file_exists(row[self._second_col])

    def _validate_tsv_format(self, filename: str) -> None:
        """Assert that a given filename has the expected tsv extensions."""
        assert any(
            filename.endswith(extension)
            for extension in self.VALID_FORMATS), (
                f"The tsv file has an unrecognized extension: {filename}\n"
                f"It should be: {', '.join(self.VALID_FORMATS)}")

    def _validate_tsv_file_exists(self, filename: str) -> None:
        """Assert that a given file exists."""
        assert Path(
            filename).is_file(), f"The tsv file seems to not exist: {filename}"

    def validate_unique_samples(self) -> None:
        """
        Assert that the combinations of sample name and tsv filenames are unique.
        """
        assert len(self._seen) == len(
            self.modified
        ), "The sample name and all tsv file names must be unique in comparison to the other rows."


def read_head(handle, num_lines: int = 10) -> str:
    """Read the specified number of lines from the current position in the file."""
    lines: List[str] = []
    for idx, line in enumerate(handle):
        if idx == num_lines:
            break
        lines.append(line)
    return "".join(lines)


def sniff_format(handle):
    """
    Detect the tabular format.

    Args:
        handle (text file): A handle to a `text file`_ object. The read position is
        expected to be at the beginning (index 0).

    Returns:
        csv.Dialect: The detected tabular format.

    .. _text file:
        https://docs.python.org/3/glossary.html#term-text-file

    """
    peek = read_head(handle)
    handle.seek(0)
    sniffer = csv.Sniffer()
    if not sniffer.has_header(peek):
        logger.critical(
            "The given sample sheet does not appear to contain a header.")
        sys.exit(1)
    dialect = sniffer.sniff(peek)
    return dialect


def check_samplesheet(file_in, file_out):
    """
    Check that the tabular samplesheet has the structure expected by nf-core pipelines.

    Validate the general shape of the table, expected columns, and each row.

    Args:
        file_in (pathlib.Path): The given tabular samplesheet. The format can be either
            CSV, TSV, or any other format automatically recognized by ``csv.Sniffer``.
        file_out (pathlib.Path): Where the validated samplesheet should be created;
            always in CSV format.
    Example:
        This function checks that the samplesheet follows the following structure:

            sample,kraken2,centrifuge
            SAMPLE1,SAMPLE1_KRAKEN2.tsv,SAMPLE1_CENTRIFUGE.tsv
            SAMPLE2,SAMPLE2_KRAKEN2.tsv,SAMPLE2_CENTRIFUGE.tsv

        or:

            sample	kraken2	centrifuge
            SAMPLE1	SAMPLE1_KRAKEN2.tsv	SAMPLE1_CENTRIFUGE.tsv
            SAMPLE2	SAMPLE2_KRAKEN2.tsv	SAMPLE2_CENTRIFUGE.tsv
    """
    required_columns: set = {"sample", "kraken2", "centrifuge"}
    # See https://docs.python.org/3.9/library/csv.html#id3 to read up on `newline=""`.
    with file_in.open(newline="") as in_handle:
        reader = csv.DictReader(in_handle, dialect=sniff_format(in_handle))
        # Validate the existence of the expected header columns.
        if not required_columns.issubset(reader.fieldnames):
            logger.critical(
                "The sample sheet **must** contain the column headers: %s.",
                ", ".join(required_columns),
            )
            sys.exit(1)
        # Validate each row.
        checker = RowChecker()
        for i, row in enumerate(reader):
            try:
                checker.validate(row)
            except AssertionError as error:
                logger.critical("%s On line %i.", str(error), i + 2)
                sys.exit(1)
        checker.validate_unique_samples()
    header = list(reader.fieldnames)
    # See https://docs.python.org/3.9/library/csv.html#id3 to read up on `newline=""`.
    with file_out.open(mode="w", newline="") as out_handle:
        writer = csv.DictWriter(out_handle, header, delimiter=",")
        writer.writeheader()
        for row in checker.modified:
            writer.writerow(row)

def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate a csv/tsv samplesheet.",
        epilog=
        "Example: python check_samplesheet.py samplesheet.csv",
    )
    parser.add_argument(
        "file_in",
        metavar="FILE_IN",
        type=Path,
        help="Tabular input samplesheet in CSV or TSV format.",
    )
    parser.add_argument(
        "file_out",
        metavar="FILE_OUT",
        type=Path,
        help="Transformed output samplesheet in CSV format.",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level,
                        format="[%(levelname)s] %(message)s")
    if not args.file_in.is_file():
        logger.error("The given input file %s was not found!", args.file_in)
        sys.exit(2)
    check_samplesheet(args.file_in, args.file_out)


if __name__ == "__main__":
    sys.exit(main())
