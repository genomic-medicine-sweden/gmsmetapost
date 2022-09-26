# GMSMetaPost

## Prerequisites

### Metadata files

For running the pipeline two metadata files are required: `samples.csv` and `samplesheet.csv`. Here are examples of how they may look like:

- **samples.csv**

```csv
sample,run_accession,instrument_platform,fastq_1,fastq_2,fasta
SRR12875558_se-SRR12875558,SRR12875558,OXFORD_NANOPORE,assets/input/se/SRR12875558_1.fastq.gz,,
SRR12875570_pe-SRR12875570,SRR12875570,ILLUMINA,assets/input/pe/SRR12875570_1.fastq.gz,assets/input/pe/SRR12875570_2.fastq.gz,
```

- **samplesheet.csv**

```csv
sample,kraken2,centrifuge,kaiju
SRR12875570_pe-SRR12875570,assets/tsvs/SRR12875570_pe-SRR12875570-kraken2.kraken2.report.tsv,assets/tsvs/SRR12875570_pe-SRR12875570-centrifuge.report.tsv,assets/tsvs/SRR12875570_pe-SRR12875570-kaiju.tsv
SRR12875558_se-SRR12875558,assets/tsvs/SRR12875558_se-SRR12875558-kraken2.kraken2.report.tsv,assets/tsvs/SRR12875558_se-SRR12875558-centrifuge.report.tsv,assets/tsvs/SRR12875558_se-SRR12875558-kaiju.tsv
```

The path to `samples.csv` must be defined in `fastq_data` parameter in `nextflow.config` and path to `samplesheet.csv` must be defined in `input` parameter.

#### Temporary metadata files containing joined taxonomic profiling

At the current stage of this pipeline additional metadata files containing joined taxonomic profiling files are required. They should be located in the root of the directory defined by `assets` parameter in `nextflow.config` file. Their names (without the `.tsv` suffix) must be identical to the sample names given in the two previously mentioned metadata files. E.g. if `assets` parameter is `assets` and one of the samples in `samples.csv` or `samplesheet.csv` is named `SRR12875558_se-SRR12875558` there must be a joined taxonomic profiling file named `assets/SRR12875558_se-SRR12875558.tsv`

These temporary metadata files can look for example the following:

```tsv
taxon_name	rpm	taxid	taxonomic_rank	classifier	centrifuge_genome_size	centrifuge_num_reads	centrifuge_abundance	kaiju_percent	kraken2_percentage_fragments_covered	kraken2_num_fragments_covered	reads_count	cami_taxid	cami_rank	cami_taxpath	cami_taxpathsn	cami_percentage
Ungulate tetraparvovirus 3	70062.2	1511916	species	centrifuge	5444	1389.0	0.0				1542
Parvovirus YX-2010/CHN	45663.1	754189	leaf	centrifuge	5444	851.0	0.0				1005
```

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

## Troubleshooting

* If you get the following error message: ```no space left on device```, make sure that that you are using:

  ```singularity.cacheDir   = "/path/to/cache"```

* If you get the following error message for `singularity`:

  ```FATAL:   While getting image info: error decoding image: invalid ObjectId in JSON```

  You are likely using an older version of singularity. You can update it with the command:

  ```conda install -c conda-forge singularity```


## Acknowledgements

This pipeline uses code and infrastructure developed and maintained by the [nf-core](https://nf-co.re) community, reused here under the [MIT license](https://github.com/nf-core/tools/blob/master/LICENSE).

> The nf-core framework for community-curated bioinformatics pipelines.
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> Nat Biotechnol. 2020 Feb 13. doi: 10.1038/s41587-020-0439-x.
> In addition, references of tools and data used in this pipeline are as follows:
