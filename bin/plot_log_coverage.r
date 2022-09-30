#!/usr/bin/env Rscript

library(tidyverse)
library(hrbrthemes)
library(plotly)
library(htmltools)

args = commandArgs(trailingOnly=TRUE)

input_tsv=args[1]
taxon=args[2]
sample=args[3]
taxid=args[4]


cov <- as_tibble(read.table(file = input_tsv)) %>% 
    rename("Position" = V2) %>% 
    rename("Coverage" = V3)

p <- cov %>% 
    select(Position, Coverage) %>% 
    ggplot(aes(Position, Coverage)) + 
    geom_area(fill="#69b3a2", alpha=0.5) + 
    geom_line(color="#69b3a2") + 
    scale_y_continuous(trans='log10') +
    theme_minimal() + 
    ggtitle(taxon) 

p <- ggplotly(p)

htmltools::save_html(p, paste(sample, ".", taxid, ".log.html", sep=""), libdir = "lib")
