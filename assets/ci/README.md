# Preparation of CI data

This document outlines shortly commands used for creating the CI test data.

## Used Conda environment

```yaml
name: ci_testing
channels:
  - conda-forge
  - bioconda
  - defaults
dependencies:
  - seqtk = 1.3
  - bwa = 0.7.17
  - minimap2 = 2.24
  - samtools = 1.15.1
  - blast = 2.13.0
  - bedtools = 2.30.0
```

## Prepare *Ungulate tetraparvovirus 3* blast database

The minimal local blast database can be created with following commands:

```bash
conda activate ci_testing
export BLASTDB=/data/BLAST_DB
TAXID=1511916
BLAST_DB_PATH=1511916_db
FASTA=1511916.fa

blastdbcmd \
-db nt \
-taxids "${TAXID}" \
-dbtype nucl > "${FASTA}"
mkdir -p "${BLAST_DB_PATH}"
cd "${BLAST_DB_PATH}"
makeblastdb \
-in ../"${FASTA}" \
-dbtype nucl \
-title "Ungulate tetraparvirus 3 db" \
-taxid "${TAXID}" \
-out "${BLAST_DB_PATH}" \
-logfile makeblastdb_"${TAXID}".log
```

-hash_index \

## Obtaining of suitable minimal fastq files

### Map all reads to *Ungulate tetraparvovirus 3* and filter out unmapped reads

#### Paired end reads

```bash
FASTQ_FILES_DIR=/home/lauri/Desktop/gmsmetapost_dev/our_fork/gmsmetapost/assets/input/
CURRENT_DIR=/home/lauri/Desktop/gmsmetapost_dev/our_fork/gmsmetapost/temp/20220907_ci_testing
cd "${CURRENT_DIR}"
mkdir bwa
bwa \
index \
-p bwa/"${TAXID}" \
"${FASTA}"

INDEX=`find -L ./ -name "*.amb" | sed 's/.amb//'`
(bwa mem \
-v 3 \
-t 92 \
"${INDEX}" \
"${FASTQ_FILES_DIR}"/pe/SRR12875570_1.fastq.gz "${FASTQ_FILES_DIR}"/pe/SRR12875570_2.fastq.gz > "${TAXID}"_pe.bam) \
&> "${TAXID}"_bwa_mem.log
(samtools sort \
-@ 47 \
-n \
"${TAXID}"_pe.bam \
| samtools view \
-f 4 \
--threads 47 \
-o "${TAXID}"_pe_filtered.bam -) \
&> "${TAXID}"_samtools_sort_view.log
rm -f "${TAXID}"_pe.bam
```

#### Single end reads

```bash
cd "${CURRENT_DIR}"
(minimap2 \
-t 92 \
-d "${TAXID}".mmi \
"${FASTA}") \
&> minimap2_index.log

(minimap2 \
-t 92 \
"${TAXID}".mmi \
"${FASTQ_FILES_DIR}"/se/SRR12875558_1.fastq.gz \
-L \
-a \
| samtools sort \
-@ 47 \
| samtools view -@ 47 \
--require-flags 4 \
-b \
-h \
-o "${TAXID}"_se_filtered.bam) \
&> minimap2_align.log
```

### Convert bam to fastq file

```bash
cd "${CURRENT_DIR}"
(bedtools bamtofastq \
-i "${TAXID}"_se_filtered.bam \
-fq "${TAXID}"_se_filtered_1.fastq) \
&> bedtools_bamtofastq_"${TAXID}"_se_filtered.log \
&
(bedtools bamtofastq \
-i "${TAXID}"_pe_filtered.bam \
-fq "${TAXID}"_pe_filtered_1.fastq \
-fq2 "${TAXID}"_pe_filtered_2.fastq) \
&> bedtools_bamtofastq_"${TAXID}"_pe_filtered.log
```

### Subset fastqs to a minimal size

For CI we'd need to have relatively small ~1Mb-50Mb fastq.gz files as test input.
The original fastq files were from [ENA](https://www.ebi.ac.uk/ena/browser/view/PRJNA670157?show=reads).

The used commands for subsampling the fastq files to a more suitable size were:

```bash
seqtk sample -s100 "${TAXID}"_pe_filtered_1.fastq 0.1 | gzip >"${TAXID}"_pe_filtered_010_1.fastq.gz &
seqtk sample -s100 "${TAXID}"_pe_filtered_2.fastq 0.1 | gzip > "${TAXID}"_pe_filtered_010_2.fastq.gz &
seqtk sample -s100 "${TAXID}"_se_filtered_1.fastq 0.01 | gzip > "${TAXID}"_se_filtered_0010_1.fastq.gz
```
