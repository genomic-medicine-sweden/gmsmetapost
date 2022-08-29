#!/usr/bin/env nextflow

// import modules
include { BWA_INDEX      } from '../../modules/local/bwa/index/main'
include { BWA_MEM        } from '../../modules/nf-core/modules/bwa/mem/main'
include { MINIMAP2_INDEX } from '../../modules/local/minimap2/index/main'
include { MINIMAP2_ALIGN } from '../../modules/nf-core/modules/minimap2/align/main'


workflow READ_MAPPING {

    take:
    reads      // [ val(meta), path(fastq), path(blastdb), path('*.fna') ]

    main:
    ch_versions = Channel.empty()
    ch_input_for_indexing = reads
                .map {
                      it ->            // Drop unneeded elements in the tuple
                      [ it[0], it[3] ] // val(meta), path(fasta)
                }
                .branch {
                se: it[0]['pairing'] == 'single_end'
                pe: it[0]['pairing'] == 'paired_end'
                }

    // ch_input_for_indexing.se.dump(tag: "se")
    // ch_input_for_indexing.pe.dump(tag: "pe")


    ch_bwa_index = BWA_INDEX( ch_input_for_indexing.pe )
    ch_versions = ch_versions.mix(BWA_INDEX.out.versions)
    // ch_bwa_index[0].dump(tag: 'bwa_i')

    ch_minimap2_index = MINIMAP2_INDEX( ch_input_for_indexing.se )
    ch_versions = ch_versions.mix(MINIMAP2_INDEX.out.versions)
    // ch_minimap2_index[0].dump(tag: 'mini_i')

    ch_prep_for_mapping = reads
                .map {
                      it ->            // Drop unneeded elements in the tuple so that cardinality is preserved for BWA_MEM
                      [ it[0], it[1] ] // val(meta), path(fastq)
                }
                .branch {
                se: it[0]['pairing'] == 'single_end'
                pe: it[0]['pairing'] == 'paired_end'
                }

    ch_input_for_pe_mapping = ch_prep_for_mapping.pe
                            .join(ch_bwa_index.index, by:0)
                            .multiMap { it ->
                                reads: [ it[0], it[1] ] // tuple val(meta), path(reads)
                                index: it[2]            // path  index
                            }

    // ch_input_for_pe_mapping.reads.dump(tag: "reads")
    // ch_input_for_pe_mapping.index.dump(tag: "index")

    ch_mapped_pe_reads = BWA_MEM( ch_input_for_pe_mapping.reads, ch_input_for_pe_mapping.index, ["sort"] )
    ch_versions = ch_versions.mix(BWA_MEM.out.versions)
    // ch_mapped_pe_reads.bam.dump(tag: "bam_pe")

    ch_input_for_se_mapping = ch_prep_for_mapping.se
                            .join( ch_minimap2_index.index, by:0 )
                            .multiMap { it ->
                                reads: [ it[0], it[1] ] // tuple val(meta), path(reads)
                                index: it[2]            // path index
                            }

    // ch_input_for_se_mapping.reads.dump(tag: "reads_se")
    // ch_input_for_se_mapping.index.dump(tag: "index_se")

    ch_mapped_se_reads = MINIMAP2_ALIGN( ch_input_for_se_mapping.reads, ch_input_for_se_mapping.index, [true], [false], [false] )
    ch_versions = ch_versions.mix(MINIMAP2_ALIGN.out.versions)
    // ch_mapped_se_reads.bam.dump(tag: "bam_se")


    ch_aligned_reads = ch_mapped_se_reads.bam
                                        .concat( ch_mapped_pe_reads.bam ) // Join into one channel all the bam files
                                        .join( reads, by:0 )              // Join by meta data: path(fastq), path(blastdb) into the channel
    // ch_aligned_reads.dump(tag: "aligned_reads_final")

    emit:
    bwa      = ch_aligned_reads  // channel: [ val(meta), path(bam), path(blastdb), path(fna) ]
    versions = ch_versions       // channel: [ versions.yml ]
}
