#!/usr/bin/env nextflow

// import modules
include { VALIDATE_TAXIDS        } from '../../modules/local/validate_taxids'
include { REMOVE_MISSING_TAXIDS  } from '../../modules/local/remove_missing_taxids'
include { DOWNLOAD_GENOMES       } from '../../modules/local/download_genomes'


workflow PREPARE_MAPPING {

    take:
    classifier_metadata      // params.filtered_hits


    main:
    ch_versions = Channel.empty()

    ch_filtered_hits = Channel.fromPath(classifier_metadata)
                            .splitCsv ( header:true )
                            .map { create_tsv_channel(it) }
    // ch_filtered_hits.dump(tag: "test")


    ch_not_found_taxids = VALIDATE_TAXIDS( ch_filtered_hits )
    ch_versions = ch_versions.mix(VALIDATE_TAXIDS.out.versions)
    // ch_not_found_taxids[0].dump(tag:'unvalidated')
    ch_excludable = ch_filtered_hits.combine(ch_not_found_taxids.txt, by:0) //.dump(tag:'combined')
    ch_taxids_validated = REMOVE_MISSING_TAXIDS( ch_excludable )
    ch_versions = ch_versions.mix(REMOVE_MISSING_TAXIDS.out.versions)
    // ch_taxids_validated[0].dump(tag:'validated')

    ch_split = ch_taxids_validated[0]
                        .map { it ->
                                    def new_meta = [:]
                                    new_meta = it[0]
                                    new_meta.remove('path')
                                    [new_meta, it[1], it[2]]
                                }
    // ch_split.dump(tag: "split_meta")
    ch_parsed = ch_split.splitCsv( header:true, sep:'\t' )
                                .map{ meta_data, fastq, row ->
                                    def meta = [:]
                                    meta.taxon     = row.taxon_name
                                    meta.taxid     = row.taxid
                                    [meta_data + meta, fastq]
                                }
    // ch_parsed.dump(tag: "split_parsed")

    ch_ref_genomes = DOWNLOAD_GENOMES( ch_parsed )
    // ch_ref_genomes[0].dump(tag: 'ref')
    ch_versions = ch_versions.mix(DOWNLOAD_GENOMES.out.versions)


    emit:
    fna = ch_ref_genomes.fna    // channel: [ val(meta), path(fna) ]
    versions = ch_versions            // channel: [ versions.yml ]
}


def create_tsv_channel(LinkedHashMap row) {
    // create meta map
    def meta = [:]
    meta.sample    = row.sample
    meta.pairing   = row.pairing

    def array = []
    if (!file(row.path).exists()) {
        exit 1, "ERROR: Please check input sheet -> classification results file does not exist!\n${row.path}"
    }
    meta.path = file(row.path)
    if (row.pairing == "single_end") {
        if (row.read2) {
            exit 1, "ERROR: Please check input sheet -> for single end reads there should not be any reverse read!\n${row.read2}"
        }
        if (!file(row.read1).exists()) {
            exit 1, "ERROR: Please check input sheet -> the single end reads file seems to not exist!\n${row.read1}"
        }
        array = [ meta, [file(row.read1)] ]
        return array
    }
    if (row.pairing == "paired_end") {
        if (!file(row.read1).exists() || !file(row.read2).exists()) {
            exit 1, "ERROR: Please check input sheet -> the one or both of the reads files seems not to exist!\n${row.read1},${row.read2}"
        }
        array = [ meta, [file(row.read1), file(row.read2)] ]
        return array
    }
    exit 1, "ERROR: Please check input sheet -> the pairing column value doesn't seem to be one of 'single_end' or 'paired_end'!\n${row.pairing}"
}
