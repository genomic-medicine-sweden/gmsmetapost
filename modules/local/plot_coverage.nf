process PLOT_COVERAGE {
    tag "$meta.sample, $meta.taxon"

    conda (params.enable_conda ? "conda-forge::r-base conda-forge::r-tidyverse conda-forge::r-plotly conda-forge::r-hrbrthemes conda-forge::r-htmltools" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'library://sofstam/gmsmetapost/gmsmetapost:latest' :
        'genomicmedicinesweden/gmsmetapost:latest' }"

    input:
    tuple val(meta), path(tsv)

    output:
    tuple val(meta), path('*html'), optional:true, emit: html
 //   path "versions.yml"           , emit: versions

    script: // This script is bundled with the pipeline, in nf-core/gmsmetapost/bin/
    """
    coverage="\$(cat $tsv | cut -f 3 | uniq | sed -n -e 'H;\${x;s/\\n/,/g;s/^,//;p;}')";
    if [[ "\$coverage" != "0" ]]; \
        then plot_coverage.r $tsv \"$meta.taxon\" $meta.sample $meta.taxid; \
    fi
    """
}