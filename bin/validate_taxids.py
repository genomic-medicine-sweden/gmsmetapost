#!/usr/bin/env python
"""Validate that all taxids in a given tsv file are downloadable from NCBI"""

import argparse
import logging
import sys
from pathlib import Path
from subprocess import run, TimeoutExpired, CalledProcessError
import os

logger = logging.getLogger()


def is_downloadable(taxid: str) -> bool:
    """Check if data from given a taxid can be downloaded

    Args:
        taxid (str): The taxid of a species which genome to test downloading
    """
    download_succeeded: bool = True
    zip_fname = f"{taxid}.zip"
    try:
        run(
            [
                "datasets",
                "download",
                "genome",
                "taxon",
                taxid,
                "--no-progressbar",
                "--dehydrated",
                "--filename",
                zip_fname,
            ],
            check=True,
            timeout=180,
        )
        logger.info("Taxid %s checked", taxid)
    except TimeoutExpired as timeout_error_msg:
        logger.error(
            "The download took too long time: %s\n%s", taxid, timeout_error_msg
        )
        download_succeeded = False
    except CalledProcessError as called_proc_error_msg:
        logger.error(
            "The return code of the downloading for taxid %s was non-zero:\n%s",
            taxid,
            called_proc_error_msg,
        )
        download_succeeded = False
    # Delete test downloaded zip file
    if download_succeeded and os.path.isfile(Path(zip_fname)):
        os.remove(zip_fname)
    return download_succeeded


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download reference genome using a taxid",
        epilog="Example: python validate_taxids.py 11665",
    )
    parser.add_argument(
        "taxid",
        metavar="TAXID_TO_VALIDATE",
        type=str,
        help="Taxid which is checked if it can be downloaded from NCBI",
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

    taxid = args.taxid
    if not is_downloadable(taxid):
        print(taxid)


if __name__ == "__main__":
    sys.exit(main())
