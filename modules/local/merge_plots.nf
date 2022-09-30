process MERGE_PLOTS {
    tag "$meta.sample"
    label 'process_low'

    conda (params.enable_conda ? "conda-forge::bash=5.0" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://containers.biocontainers.pro/s3/SingImgsRepo/biocontainers/v1.2.0_cv2/biocontainers_v1.2.0_cv2.img' :
        'biocontainers/biocontainers:v1.2.0_cv2' }"

    input:
    tuple val(meta), path(html)

    output:
    tuple val(meta), path('*html'), emit: html

    script:
    """
    if [[ "${html.baseName}" == *"log"* ]];
    then 
        cat $html >> ${meta.sample}.log.html;
    else
        cat $html >> ${meta.sample}.default.html; 
    fi
    """
}