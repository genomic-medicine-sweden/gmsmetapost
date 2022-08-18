process REMOVE_MISSING_TAXIDS {
    tag "${meta.sample}"

    conda (params.enable_conda ? "conda-forge::python>=3.9 conda-forge::pydantic=1.9.1 conda-forge::ncbi-datasets-cli=13.35.0 conda-forge::parallel=20220722 " : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'library://ljmesi/gmsmetapost/datasets_pydantic:20220815' :
        'docker://genomicmedicinesweden/gmsmetapost-download-genomes:latest' }"

    input:
    tuple val(meta), path(fastq), path(txt)

    output:
    tuple val(meta), path(fastq), path('*.validated.tsv'), emit: tsv
    path "versions.yml"                                  , emit: versions

    script:
    """
    cp $meta.path bak.tsv
    cat $txt \
    | parallel --jobs 1 --verbose \"sed -i '/\t{}\t/d' $meta.path\"
    mv $meta.path ${meta.sample}.validated.tsv
    mv bak.tsv $meta.path

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
        pydantic: \$(python -c 'import pydantic; print(pydantic.__version__)')
        ncbi-datasets-cli: \$(datasets version | sed -n '/^1.*/p')
        GNU parallel: \$(parallel --version | head -n 1 | sed 's/GNU parallel //')
        sed: \$(sed --version | head -n 1 | sed 's/sed //')
    END_VERSIONS
    """
}
