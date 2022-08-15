#!/usr/bin/env python
"""Download a genome sequence using NCBI taxid."""

import argparse
import logging
import sys
from pathlib import Path
from subprocess import run, TimeoutExpired, CalledProcessError
import json
import zipfile
from datetime import datetime
from typing import Optional
import shutil
from pydantic import BaseModel, validator


logger = logging.getLogger()


# Classes for modeling one line json:s
class AssemblyInfo(BaseModel):
    """Model for all NCBI assembly info"""

    assemblyAccession: str
    assemblyLevel: str
    assemblyName: str
    assemblyStatus: str
    assemblyType: str
    currentAssemblyAccession: str
    genbankAssmAccession: str
    submissionDate: datetime

    @validator("submissionDate", pre=True)
    @classmethod
    def parse_submission_date(cls, value: str) -> datetime:
        """Convert a string of e.g. '1993-09-29' to datetime.datetime object
        if parsable

        Args:
            value (str): A date string e.g. '1993-09-29'

        Returns:
            datetime: datetime object or if input was not str anything
        """
        return datetime.strptime(value, "%Y-%m-%d") if isinstance(value, str) else value


class AssemblyStats(BaseModel):
    """Model for all NCBI assembly stats info"""

    contigL50: int
    contigN50: int
    gcCount: int
    numberOfComponentSequences: int
    numberOfContigs: int
    numberOfScaffolds: int
    scaffoldL50: int
    scaffoldN50: int
    totalNumberOfChromosomes: int
    totalSequenceLength: int
    totalUngappedLength: int


class AnnotationInfo(BaseModel):
    """Model for all NCBI annotation info"""

    name: str
    releaseDate: datetime
    stats: dict

    @validator("releaseDate", pre=True)
    @classmethod
    def parse_submission_date(cls, value: str) -> datetime:
        """Convert a string of e.g. '1993-09-29' to datetime.datetime object
        if parsable

        Args:
            value (str): A date string e.g. '1993-09-29'

        Returns:
            datetime: datetime object or if input was not str anything
        """
        return datetime.strptime(value, "%Y-%m-%d") if isinstance(value, str) else value


class Assembly(BaseModel):
    """Model for all NCBI info relating to the retrieved assembly"""

    annotationInfo: Optional[AnnotationInfo]
    assemblyInfo: AssemblyInfo
    assemblyStats: AssemblyStats
    organismName: str
    taxId: str = ""


def sort_assemblies(assemblies: list[Assembly]) -> list[Assembly]:
    """
    Sort assemblies by date and return them in a list from newest to oldest

    Args:
        assemblies (list[Assembly]): List of pydantic Assemblies

    Returns:
        list[Assembly]: Sorted list of assemblies
    """
    return sorted(assemblies, key=lambda x: x.assemblyInfo.submissionDate, reverse=True)


def download_genomes_zip(taxid: str, extra_arg: str = "--no-progressbar") -> None:
    """Download genome assembly based on given taxid

    Args:
        taxid (str): The taxid of a species which genome to download
    """
    run(
        [
            "datasets",
            "download",
            "genome",
            "taxon",
            taxid,
            "--exclude-gff3",
            "--exclude-protein",
            "--exclude-rna",
            "--exclude-genomic-cds",
            extra_arg,
            "--filename",
            f"{taxid}.zip",
        ],
        check=True,
        timeout=600,  # Download for 10 minutes before erroring out
    )


def unzip(zipped_file: Path, unzip_dir: Path = Path.cwd()) -> None:
    """Unzip a file into a given path

    Args:
        zipped_file (Path): Path to the file to be zipped
        unzip_dir (Path, optional): Path to the directory where
            the zipped file should be unzipped. Defaults to Path.cwd()
    """
    with zipfile.ZipFile(zipped_file, "r") as zip_ref:
        zip_ref.extractall(unzip_dir)


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download reference genome using a taxid",
        epilog="Example: python download_ref_genome.py 11665",
    )
    parser.add_argument(
        "taxid",
        metavar="TAXID",
        type=str,
        help="Taxid of a species which genome to download.",
    )
    parser.add_argument(
        "-j",
        "--jsonl-file",
        metavar="jsonl-file",
        type=Path,
        help="Path to '.jsonl' file with info about all the different assemblies retrieved.",
        default=Path("ncbi_dataset/data/assembly_data_report.jsonl"),
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="ERROR",
    )
    return parser.parse_args(argv)


def open_jsonl_file(jsonl_file: Path) -> list[Assembly]:
    """Parse a one line json list file

    Args:
        jsonl_file (Path): Path to one line json list file

    Returns:
        list[Assembly]: List of parsed assembly infos
    """
    json_list: list = []
    with open(jsonl_file, encoding="utf8") as assembly_data_report:
        # Iterate over all json lines
        for single_line_json in assembly_data_report:
            json_dict: dict = json.loads(single_line_json)
            json_list.append(Assembly(**json_dict))
    return json_list


def get_assembly_accession(assembly: Assembly) -> str:
    """Extract Accession ID from assembly metadata

    Args:
        assembly (Assembly): All assembly metadata

    Returns:
        str: Accession ID, e.g. 'GCF_000847605.1'
    """
    return assembly.assemblyInfo.assemblyAccession


def extract_assembly_file_path(assembly_path_dir: Path) -> Path:
    """Extract from a given path, a path to a genome assembly

    Args:
        assembly_path_dir (Path): Directory where the genome assembly file should exist

    Raises:
        FileNotFoundError: Error raised when no '.fna' file is found in the given directory

    Returns:
        Path: Path to the '.fna' genome assembly file
    """
    if list(assembly_path_dir.glob("*.fna")):
        # There should be only one assembly .fna file in the directory
        num_fnas: int = len(list(assembly_path_dir.glob("*.fna")))
        assert num_fnas == 1, f"Too many or few assembly files {num_fnas}"
        return list(assembly_path_dir.glob("*.fna"))[0]
    raise FileNotFoundError(
        f"No '.fna' assembly files found in: {str(assembly_path_dir)}"
    )


def copy_assembly_file(assembly_path: Path, path_to_move_assembly_to: Path) -> None:
    """Copy assembly from its original directory to another location

    Args:
        assembly_path (Path): Directory where the assembly (.fna) file resides
        path_to_move_assembly_to (Path): Directory to which the assembly file should be copied
    """
    if assembly_path.is_file():
        shutil.copy(assembly_path, path_to_move_assembly_to)
        logger.info(
            "Copying %s to: %s", str(assembly_path), str(path_to_move_assembly_to)
        )
    else:
        raise FileNotFoundError(f"No '.fna' file could be found: {str(assembly_path)}")


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")

    taxid: str = args.taxid
    download_succeeded: bool = True
    try:
        download_genomes_zip(taxid)
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

    if download_succeeded:
        unzip(Path(f"{taxid}.zip"))
        assemblies: list[Assembly] = sort_assemblies(open_jsonl_file(args.jsonl_file))
        # Handle the case if the latest assembly doesn't contain an assembly .fna file
        for assembly in assemblies:
            accession: str = get_assembly_accession(assembly)
            latest_assembly_path: Path = Path.cwd() / f"ncbi_dataset/data/{accession}"
            try:
                assembly_path_checked = extract_assembly_file_path(latest_assembly_path)
            except FileNotFoundError:
                logger.error(
                    "No assembly file existed in path: %s",
                    latest_assembly_path,
                )
                continue
            break
        if assembly_path_checked:
            copy_assembly_file(assembly_path_checked, Path.cwd())
        else:
            logger.error("No assembly files were found for taxid: %s", taxid)


if __name__ == "__main__":
    sys.exit(main())
