process PLOT_COVERAGE {
    tag "$meta.sample, $meta.taxon"

    conda (params.enable_conda ? "conda-forge::r-base conda-forge::r-tidyverse conda-forge::r-plotly conda-forge::r-hrbrthemes conda-forge::r-htmltools" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'library://sofstam/gmsmetapost/gmsmetapost:latest' :
        'genomicmedicinesweden/gmsmetapost:latest' }"

    input:
    tuple val(meta), path(tsv)

    output:
    tuple val(meta), path('*html'), emit: html
 //   path "versions.yml"           , emit: versions

    script: // This script is bundled with the pipeline, in nf-core/gmsmetapost/bin/
    """
    #!/usr/bin/env Rscript

    library(tidyverse)
    library(hrbrthemes)
    library(plotly)
    library(htmltools)

    input_tsv="$tsv"

    cov <- as_tibble(read.table(file = input_tsv)) \
        %>% rename("Position" = V2) \
        %>% rename("Coverage" = V3)

    p <- cov %>% select(Position, Coverage) %>% \
        ggplot(aes(Position, Coverage)) + \
        geom_area(fill="#69b3a2", alpha=0.5) + \
        geom_line(color="#69b3a2") + \
        theme_minimal() + \
        ggtitle("${meta.taxon}") 

    p <- ggplotly(p)

    htmltools::save_html(p, "${meta.sample}.${meta.taxid}.html")
    
    """
}