process VALIDATE_TAXIDS {
    tag "${meta.sample}"

    conda (params.enable_conda ? "conda-forge::python>=3.9 conda-forge::pydantic=1.9.1 conda-forge::ncbi-datasets-cli=13.35.0 conda-forge::parallel=20220722 " : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'library://ljmesi/gmsmetapost/datasets_pydantic:20220815' :
        'docker://genomicmedicinesweden/gmsmetapost-download-genomes:latest' }"

    input:
    tuple val(meta), path(tsv)

    output:
    tuple val(meta), path('excludable_taxids.txt'), emit: txt
    path "versions.yml"                           , emit: versions

    script: // This script is bundled with the pipeline, in nf-core/gmsmetapost/bin/
    """
    cat $meta.path \
    | parallel --header : --colsep '\t' \
    validate_taxids.py {taxid} \
    >> excludable_taxids.txt

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
        pydantic: \$(python -c 'import pydantic; print(pydantic.__version__)')
        ncbi-datasets-cli: \$(datasets version | sed -n '/^1.*/p')
        GNU parallel: \$(parallel --version | head -n 1 | sed 's/GNU parallel //)')
    END_VERSIONS
    """
}
