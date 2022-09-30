#!/usr/bin/env nextflow

//
// Plot coverage of metagenomic reads against reference genomes
//

// import modules
include { SAMTOOLS_DEPTH        } from '../../modules/nf-core/modules/samtools/depth/main'
include { PLOT_COVERAGE         } from '../../modules/local/plot_coverage'

workflow GENERATE_PLOTS {

    take:
    bwa // channel: [ val(meta), path(bam), path(blastdb), path(fna) ]


    main:
    ch_versions = Channel.empty()

    
    ch_input_for_samtools = bwa
                .map {
                    it ->               // Drop unneeded elements in the tuple
                    [ it[0], it[1] ]    // val(meta), path(bam)
                }

    ch_sam = SAMTOOLS_DEPTH( ch_input_for_samtools )
    ch_versions = ch_versions.mix(SAMTOOLS_DEPTH.out.versions)

    ch_ind_plots = PLOT_COVERAGE( ch_sam.tsv )
    // ch_ind_plots.html.dump(tag: "cov_plots")

    ch_versions = ch_versions.mix(PLOT_COVERAGE.out.versions)

    emit:
    depth    = ch_sam.tsv
    plots    = ch_ind_plots.html
    versions = ch_versions

}

