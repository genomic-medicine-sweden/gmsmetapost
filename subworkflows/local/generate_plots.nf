#!/usr/bin/env nextflow

//
// Plot coverage of metagenomic reads against reference genomes
//

// import modules
include { SAMTOOLS_DEPTH    } from '../../modules/nf-core/modules/samtools/depth/main'
include { PLOT_COVERAGE     } from '../../modules/local/plot_coverage'
include { PLOT_COVERAGE_LOG } from '../../modules/local/plot_coverage_log'
include { MERGE_PLOTS       } from '../../modules/local/merge_plots'

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

    ch_def_plots = PLOT_COVERAGE( ch_sam.tsv )
    ch_log_plots = PLOT_COVERAGE_LOG( ch_sam.tsv )

    ch_versions = ch_versions.mix(PLOT_COVERAGE.out.versions)

    ch_def_plots.html
                // Remap meta so it excudes taxon information
                // so that we can group by meta to combine outputs
                .map{ 
                    meta, html ->
                    meta_subset = ["sample": meta.sample, 
                                    "instrument_platform": meta.instrument_platform,
                                    "pairing": meta.pairing,
                                    ]
                    [meta_subset, html]
                    }
                .groupTuple(by: [0])
                .set{ ch_def_plots_grouped }

    // Repeat for the log_scale plots as well
    ch_log_plots.html
                // Remap meta so it excudes taxon information
                // so that we can group by meta to combine outputs
                .map{ 
                    meta, html ->
                    meta_subset = ["sample": meta.sample, 
                                    "instrument_platform": meta.instrument_platform,
                                    "pairing": meta.pairing,
                                    ]
                    [meta_subset, html]
                    }
                .groupTuple(by: [0])
                .set{ ch_log_plots_grouped }


    ch_plots = ch_def_plots_grouped
                                .concat( ch_log_plots_grouped )

    ch_plots.dump(tag: "grouped")

    ch_merge_plots = MERGE_PLOTS( ch_plots ) 

    emit:
    depth    = ch_sam.tsv
    plots    = ch_merge_plots
    versions = ch_versions

}
