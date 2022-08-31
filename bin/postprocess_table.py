#!/usr/bin/env python
"""Post-process hits table so that it can be readily used for downloading genomes."""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
import tempfile
from subprocess import run, TimeoutExpired, CalledProcessError

from tomlkit import boolean


logger = logging.getLogger()


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Postprocess hits table so that it can be readily used for downloading genomes",
        epilog="Example: postprocess_filtered_table.py SRR12875570_pe-SRR12875570.tsv SRR12875570_pe-SRR12875570.postprocessed.tsv",
    )
    parser.add_argument(
        "input",
        metavar="INPUT",
        type=Path,
        help="Tsv file containing unprocessed hits table",
    )
    parser.add_argument(
        "output",
        metavar="OUTPUT",
        type=Path,
        help="Tsv file containing post-processed hits table",
    )
    parser.add_argument(
        "-t",
        "--ncbi-taxon-db",
        metavar="Path",
        type=Path,
        default=Path("../temp/taxdump"),
        help="Path to NCBI taxonomy database",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )
    return parser.parse_args(argv)


def get_unique_taxid_list(
    df: pd.DataFrame, col_name: str = "taxid", classifier_name: str = ""
) -> list[str]:
    """Get a deduplicated list of taxids

    Args:
        df (pd.DataFrame): DataFrame where to extract the taxids
        col_name (str, optional): Column name where the taxids are located. Defaults to "taxid".
        classifier_name (str, optional): Name of the classifier which taxids we want to extract. If not given uses all classifiers. Defaults to "".

    Returns:
        list[str]: Deduplicated list of taxids of given classifier
    """
    if classifier_name:
        taxid_col: pd.Series = df[col_name][df["classifier"] == classifier_name]
    else:
        taxid_col: pd.Series = df[col_name]
    taxid_col.dropna(inplace=True)
    return list(set(taxid_col.tolist()))


def run_taxonkit_lineage(
    temp_taxid_file: Path, db: Path, no_lineage: bool, show_name: bool
) -> str:
    """Run taxonkit lineage on a list of taxids file

    Args:
        temp_taxid_file (Path): Path to NamedTemporaryFile where taxids are each on one row
        db (Path): Path to NCBI taxonomy database (necessary for taxonkit to work)
        no_lineage (bool): Whether to exclude lineage information from the output
        show_name (bool): Whether to show scientific name in the last column

    Returns:
        str: Stdout from taxonkit lineage run
    """
    run_cmd = [
        "taxonkit",
        "lineage",
        temp_taxid_file,
        "--data-dir",
        db,
        "--show-rank",
    ]
    if no_lineage:
        run_cmd.append("--no-lineage")
    if show_name:
        run_cmd.append("--show-name")
    try:
        result = run(
            run_cmd,
            check=True,
            timeout=180,
            capture_output=True,
            text=True,
        )
    except TimeoutExpired as timeout_error_msg:
        logger.error(
            "Running taxonkit took too long time for file: %s\n%s",
            temp_taxid_file,
            timeout_error_msg,
        )
        sys.exit(1)
    except CalledProcessError as called_proc_error_msg:
        logger.error(
            "The return code of the program run for file %s was non-zero: \n%s",
            temp_taxid_file,
            called_proc_error_msg,
        )
        sys.exit(2)
    if result.stdout:
        return result.stdout
    logger.error(
        "The program run for file %s didn't produce any output:", temp_taxid_file
    )
    sys.exit(3)


def get_taxonkit_lineage_results(
    taxids: list[str], db: Path, no_lineage: bool, show_name: bool
) -> str:
    """Run taxonkit lineage on given list of taxids

    Args:
        taxids (list[str]): List of taxids which should be run with taxonkit lineage
        db (Path): Path to the NCBI taxonomy database (necessary for taxonkit to work)
        no_lineage (bool): Whether to exclude lineage information from the output
        show_name (bool): Whether to show scientific name in the last column

    Returns:
        str: Tab delimited table of taxids and sci names
    """
    # Populate file with taxids
    with tempfile.NamedTemporaryFile() as fp:
        for taxid in taxids:
            fp.write(str.encode(f"{taxid}\n"))
        fp.seek(0)
        return run_taxonkit_lineage(Path(fp.name), db, no_lineage, show_name)


def parse_taxonkit_results(results: str) -> list[str]:
    """Parse taxonkit lineage results to a list of lists

    Args:
        results (str): A STDOUT from 'taxonkit lineage taxids.txt' command

    Returns:
        list[str]: List of lists of strings with each element containing one parsed row of taxonkit results
    """
    return [x.split("\t") for x in results.split("\n") if x]


def get_taxids_of_superkingdom(
    parsed_results: list[list[str]], kingdom: str
) -> list[str]:
    """Get a list of taxids of given superkingdom

    Args:
        results (str): Parsed taxonkit lineage results
        kingdom (str): The kingdom which taxids are returned

    Returns:
        list[str]: Taxids from the user given kingdom
    """
    return [parsed_row[0] for parsed_row in parsed_results if kingdom in parsed_row[1]]


def get_taxids_of_excluded_ranks(
    parsed_results: list[list[str]], ranks_to_exclude: list[str]
) -> list[str]:
    """Pick out taxids from parsed taxonkit lineage results belonging to excluded ranks

    Args:
        parsed_results (list[list[str]]): List of parsed taxonkit lineage results rows
        ranks_to_exclude (list[str]): List of taxids of ranks that we don't want to keep

    Returns:
        list[str]: List of taxids belonging to ranks that we want to exclude
    """
    return [
        parsed_row[0]
        for parsed_row in parsed_results
        if parsed_row[3] in ranks_to_exclude
    ]


def read_input_table(tsv: Path) -> pd.DataFrame:
    """Read input tsv file into a DataFrame

    Args:
        tsv (Path): Path to the tsv file

    Returns:
        pd.DataFrame: DataFrame of the tsv table
    """
    data_types: dict = {
        "taxon_name": str,
        "rpm": float,
        "taxid": str,
        "taxonomic_rank": str,
        "classifier": str,
        "centrifuge_genome_size": str,
        "centrifuge_num_reads": str,
        "centrifuge_abundance": float,
        "kaiju_percent": float,
        "kraken2_percentage_fragments_covered": float,
        "kraken2_num_fragments_covered": str,
        "reads_count": int,
        "cami_taxid": str,
        "cami_rank": str,
        "cami_taxpath": str,
        "cami_taxpathsn": str,
        "cami_percentage": float,
    }
    logger.info("Reading %s tsv file into a DataFrame", tsv)
    return pd.read_table(tsv, index_col=False, dtype=data_types)


def main(argv=None):
    """Coordinate program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")

    # Read input tsv file
    input_tsv: Path = args.input
    if not input_tsv.is_file():
        logger.error("The given input file %s was not found!", input_tsv)
        sys.exit(1)
    df = read_input_table(input_tsv)

    # Exchange non-descriptive taxon names such as "taxonid:297" to
    # "Hydrogenophilus thermoluteolus" in kaiju output results rows
    kaiju_taxids: list[str] = get_unique_taxid_list(df, classifier_name="kaiju")
    kaiju_taxonkit_results = get_taxonkit_lineage_results(
        kaiju_taxids, args.ncbi_taxon_db, no_lineage=True, show_name=True
    )
    parsed_kaiju_tax_results: list[list[str]] = parse_taxonkit_results(
        kaiju_taxonkit_results
    )
    kaiju_taxonomy_mappings: dict = {
        f"taxonid:{taxon_name[0]}": taxon_name[1]
        for taxon_name in parsed_kaiju_tax_results
    }
    df.replace({"taxon_name": kaiju_taxonomy_mappings}, inplace=True)

    # Get a list of taxids belonging to the wanted kingdom
    all_unique_taxids: list[str] = get_unique_taxid_list(df)
    taxonkit_results: str = get_taxonkit_lineage_results(
        all_unique_taxids, args.ncbi_taxon_db, no_lineage=False, show_name=True
    )
    parsed_tax_results: list[list[str]] = parse_taxonkit_results(taxonkit_results)
    viral_taxids: list[str] = get_taxids_of_superkingdom(parsed_tax_results, "Viruses")

    # Get a list of taxids of unwanted ranks
    ranks_to_exclude: list[str] = [
        "superkingdom",
        "clade",
        "kingdom",
        "phylum",
        "class",
        "order",
        "suborder",
        "family",
        # "subfamily","genus","subgenus","species","no rank"
    ]
    excluded_taxids: list[str] = get_taxids_of_excluded_ranks(
        parsed_tax_results, ranks_to_exclude
    )

    # Keep only rows with wanted taxids
    viral_taxids_after_exluded_ranks: list[str] = list(
        set(viral_taxids).difference(set(excluded_taxids))
    )
    df = df[df.taxid.isin(viral_taxids_after_exluded_ranks) == True]

    # Drop rows with duplicate taxids, keep the first occurence of these rows
    df.drop_duplicates(subset=["taxid"], keep="first", inplace=True)

    # Print to tsv file
    df.to_csv(args.output, sep="\t", index=False)


if __name__ == "__main__":
    sys.exit(main())
