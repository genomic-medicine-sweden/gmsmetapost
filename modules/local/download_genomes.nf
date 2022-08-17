process DOWNLOAD_GENOMES {
    tag "$meta.taxon: $meta.taxid"

    conda (params.enable_conda ? "conda-forge::python>=3.9 conda-forge::pydantic=1.9.1 conda-forge::ncbi-datasets-cli=13.35.0 " : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'library://ljmesi/gmsmetapost/datasets_pydantic:20220815' :
        'docker://genomicmedicinesweden/gmsmetapost-download-genomes:latest' }"

    input:
    tuple val(meta), path(fastq)

    output:
    tuple val(meta), path(fastq), path('*.fna'), emit: fna
    path "versions.yml"                        , emit: versions

    script: // This script is bundled with the pipeline, in nf-core/gmsmetapost/bin/
    """
    download_ref_genome.py \
        $meta.taxid

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
        pydantic: \$(python -c 'import pydantic; print(pydantic.__version__)')
        ncbi-datasets-cli: \$(datasets version | sed -n '/^1.*/p')
    END_VERSIONS
    """
}
