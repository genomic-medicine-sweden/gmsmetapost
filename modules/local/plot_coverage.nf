process PLOT_COVERAGE {
    tag "${meta.sample}" // DOUBLE CHECK THIS BIT

    conda (params.enable_conda ? "conda-forge::r conda-forge::r-tidyverse conda-forge::r-plotly" : null)
   // container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?  
   //     'https://depot.galaxyproject.org/singularity/r-tidyverse:1.2.1' :
   //     'quay.io/biocontainers/r-tidyverse:1.2.1' }"
    // UPDATE CONTAINERS

    // WHAT IS THE DIFFERENCE BETWEEN path(tsv) and path(*tsv)
    input:
    tuple val(meta), path(tsv)

    output:
    tuple val(meta), path('html'), emit: html
    path "versions.yml"                           , emit: versions

    script: 
    """
    #!/usr/bin/env Rscript
	library(tidyverse)
	library(plotly)
    library(htmlwidgets)

    cov <- as_tibble(read.table(file = "${tsv}")) \
        %>% rename("Position" = V2) \
        %>% rename("Coverage" = V3)

    p <- cov %>% select(Position, Coverage) \ 
        %>% ggplot(aes(Position, Coverage)) \  
        + geom_line() \ 
        + ggtitle("${meta.taxon}") 

    ggplotly(p)



    """
