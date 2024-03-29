process VALIDATE_TAXIDS {
    tag "${meta.sample}"

    conda (params.enable_conda ? "conda-forge::python>=3.9 bioconda::blast=2.13.0 conda-forge::parallel=20220722 " : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'library://sofstam/gmsmetapost/gmsmetapost:latest' :
        'genomicmedicinesweden/gmsmetapost:latest' }"
        
    input:
    tuple val(meta), path(fastq), path(blastdb)

    output:
    tuple val(meta), path('*excludable_taxids.txt'), emit: txt
    path "versions.yml"                           , emit: versions

    script:
    """
    blast_retrieve () {
        DB_FNAME=`find -L ./ -name '*.nhr'`
        FIRST_FN=`echo \$DB_FNAME | awk '{print \$1;}'`
        DB=`basename \$FIRST_FN | sed 's/\\..*//'`
        (cd $blastdb
        blastdbcmd \
        -taxids \$1 \
        -dbtype nucl \
        -db \$DB \
        > /dev/null) \
        || echo \$1
    }

    export -f blast_retrieve

    cat $meta.path \
    | parallel --header : --colsep '\t' \
    blast_retrieve {taxid} >> ${meta.sample}_excludable_taxids.txt

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        BLAST: \$(blastdbcmd -version 2>&1 | sed 's/^.*blastdbcmd: //; s/ .*\$//')
        GNU parallel: \$(parallel --version | head -n 1 | sed 's/GNU parallel //)')
    END_VERSIONS
    """
}
