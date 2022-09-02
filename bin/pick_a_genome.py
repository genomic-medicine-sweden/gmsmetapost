#!/usr/bin/env python
"""Find from a multifasta file longest and most complete sequence and write it into a fasta file"""

import argparse
import logging
import sys
from pathlib import Path
from Bio import SeqIO

logger = logging.getLogger()


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Find from a multifasta file longest and most complete sequence and write it into a fasta file",
        epilog="Example: python pick_a_genome.py multifasta.fna singlefasta.fna",
    )
    parser.add_argument(
        "input_multifasta",
        metavar="INPUT-MULTIFASTA",
        type=Path,
        help="Input multifasta file",
    )
    parser.add_argument(
        "output_singlefasta",
        metavar="OUTPUT-SINGLEFASTA",
        type=Path,
        help="Output single fasta file",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="ERROR",
    )
    return parser.parse_args(argv)


def find_seqs_by_description(
    seqio_obj: SeqIO.SeqRecord, key_phrase: str
) -> SeqIO.SeqRecord:
    """Find SeqIO.SeqRecord instance with a matching key phrase

    Args:
        seqio_obj (SeqIO.SeqRecord): SeqIO.SeqRecord object containing a record description
        key_phrase (str): Key phrase to search in a record description

    Returns:
        SeqIO.SeqRecord: Object with the matching key phrase in the description
    """ """"""
    if key_phrase in seqio_obj.description:
        return seqio_obj


def sort_records_by_len(
    seq_records: list[SeqIO.SeqRecord],
) -> list[SeqIO.SeqRecord]:
    """Sort a list of SeqIO.SeqRecord objects by their sequence length

    Args:
        seq_records (list[SeqIO.SeqRecord]): A list of SeqIO.SeqRecord

    Returns:
        list[SeqIO.SeqRecord]: A by sequence length sorted list of SeqIO.SeqRecord
    """
    return sorted(seq_records, key=lambda rec: len(rec), reverse=True)


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")

    input_multifasta: Path = args.input_multifasta
    if not input_multifasta.is_file():
        logger.error("The given input file %s was not found!", input_multifasta)
        sys.exit(1)

    COMPLETENESS_LEVELS: list[str] = [
        "complete genome",
        "complete cds",
        "partial genome",
        "partial cds",
        "allele",
    ]
    # Keep track of if a sequence of given completeness was found for logging purposes
    completeness_level_found: bool = False
    # Iterate through the records in the order of descending completeness level
    for completeness_level in COMPLETENESS_LEVELS:
        # Find all records of given completeness level
        if seq_records := [
            find_seqs_by_description(seq_record, completeness_level)
            for seq_record in SeqIO.parse(input_multifasta, "fasta")
            if find_seqs_by_description(seq_record, completeness_level) is not None
        ]:
            completeness_level_found = True
            sorted_seq_records: list[SeqIO.SeqRecord] = sort_records_by_len(seq_records)
            longest_seq_record: SeqIO.SeqRecord = sorted_seq_records[0]
            logger.info(
                "A record with ID: '%s' and with '%s' completeness level picked.",
                longest_seq_record.id,
                completeness_level,
            )
            logger.info(
                "Record description: %s\nRecord ID: %s\nRecord length: %s",
                longest_seq_record.description,
                longest_seq_record.id,
                str(len(longest_seq_record)),
            )
            # Write the longest and most complete fasta record into a file
            SeqIO.write(longest_seq_record, args.output_singlefasta, "fasta")
            break  # Jump out of the for loop when we've found the longest sequence of highest completeness
        else:
            logger.warning(
                "There weren't any records with '%s' completeness level",
                completeness_level,
            )
    if not completeness_level_found:
        logger.error(
            "There weren't any records with these '%s' completeness levels",
            ", ".join(COMPLETENESS_LEVELS),
        )


if __name__ == "__main__":
    sys.exit(main())
