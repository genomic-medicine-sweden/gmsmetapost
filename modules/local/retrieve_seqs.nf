process RETRIEVE_SEQS {
    tag "$meta.sample, $meta.taxon: $meta.taxid"

    conda (params.enable_conda ? "conda-forge::python>=3.9 " : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'library://ljmesi/gmsmetapost/general:20220825' :
        'genomicmedicinesweden/gmsmetapost:latest' }"

    input:
    tuple val(meta), path(fastq), path(blastdb)

    output:
    tuple val(meta), path(fastq), path(blastdb), path('*.fna'), emit: fna
    path "versions.yml"                                       , emit: versions

    script: // This script is bundled with the pipeline, in nf-core/gmsmetapost/bin/
    """
    (cd $blastdb
    blastdbcmd \
    -db nt \
    -taxids $meta.taxid \
    -dbtype nucl) \
    > ${meta.taxid}_${meta.sample}.fna

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        BLAST: \$(blastdbcmd -version 2>&1 | sed 's/^.*blastdbcmd: //; s/ .*\$//')
    END_VERSIONS
    """
}
