# GMSMetaPost

## Prerequisites

### Metadata files

Two metadata files are required `assets/samples.csv` and `assets/samplesheet.csv`. Here are examples of how they may look like:

- **assets/samples.csv**

```csv
sample,path,pairing,read1,read2
SRR12875558_se-SRR12875558,assets/SRR12875558_se-SRR12875558.tsv,single_end,assets/input/se/SRR12875558_1.fastq.gz
SRR12875570_pe-SRR12875570,assets/SRR12875570_pe-SRR12875570.tsv,paired_end,assets/input/pe/SRR12875570_1.fastq.gz,assets/input/pe/SRR12875570_2.fastq.gz
```

- **assets/samplesheet.csv**

```csv
sample,kraken2,centrifuge,kaiju
sample1,assets/tsvs/SRR12875570_pe-SRR12875570-kraken2.kraken2.report.tsv,assets/tsvs/SRR12875570_pe-SRR12875570-centrifuge.report.tsv,assets/tsvs/SRR12875570_pe-SRR12875570-kaiju.tsv
sample2,assets/tsvs/SRR12875558_se-SRR12875558-kraken2.kraken2.report.tsv,assets/tsvs/SRR12875558_se-SRR12875558-centrifuge.report.tsv,assets/tsvs/SRR12875558_se-SRR12875558-kaiju.tsv
```

The path to `assets/samples.csv` should be defined in `filtered_hits` parameter in `nextflow.config` or on the command line.

### BLAST nt database

GMSMetaPost requires a local version of BLAST nt database. The easiest way to aqcuire it is by downloading with [`blast v.2.13.0`](http://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastDocs) utility `update_blastdb.pl`:

```bash
update_blastdb.pl \
--decompress \
nt
```

In addition the latest taxonomy database is required as well. It should be downloaded into the same directory:

```bash
wget --continue https://ftp.ncbi.nlm.nih.gov/blast/db/taxdb.tar.gz
rm taxdb.btd taxdb.bti
tar xvf taxdb.tar.gz
rm -f taxdb.tar.gz
```

It is also recommended to update regularly the local BLAST nt database with command:

```bash
update_blastdb.pl \
nt
```

Finally, the user should define the path to the database by either defining `blast_db` parameter in `nextflow.config` or on the command line.

## Running GMSMetaPost

GMSMetaPost can be run with command:

```bash
nextflow run main.nf \
--input assets/samplesheet.csv \
--outdir test \
-profile conda
```

`conda` profile can also be replaced by `singularity` or `docker`.

## Acknowledgements

This pipeline uses code and infrastructure developed and maintained by the [nf-core](https://nf-co.re) community, reused here under the [MIT license](https://github.com/nf-core/tools/blob/master/LICENSE).

> The nf-core framework for community-curated bioinformatics pipelines.
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> Nat Biotechnol. 2020 Feb 13. doi: 10.1038/s41587-020-0439-x.
> In addition, references of tools and data used in this pipeline are as follows:
