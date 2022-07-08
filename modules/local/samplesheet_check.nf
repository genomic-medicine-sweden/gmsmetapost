process SAMPLESHEET_CHECK {
    tag "$samplesheet"

    //conda (params.enable_conda ? "conda-forge::python=3.8.3" : null)
    //container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
    //    'https://depot.galaxyproject.org/singularity/python:3.8.3' :
    //    'quay.io/biocontainers/python:3.8.3' }"
    conda (params.enable_conda ? "conda-forge::pandas=1.1.5" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/pandas:1.1.5' :
        'quay.io/biocontainers/pandas:1.1.5' }"

    input:
    path samplesheet

    output:
    path '*.csv'       , emit: csv
    path "versions.yml", emit: versions

    script: // This script is bundled with the pipeline, in nf-core/gmsmetapost/bin/
    """
    check_samplesheet.py \\
        $samplesheet \\
        samplesheet.valid.csv
    calculate_abundance.py $samplesheet

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
