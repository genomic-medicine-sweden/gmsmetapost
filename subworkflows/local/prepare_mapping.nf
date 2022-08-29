#!/usr/bin/env nextflow

// import modules
include { VALIDATE_TAXIDS        } from '../../modules/local/validate_taxids'
include { REMOVE_MISSING_TAXIDS  } from '../../modules/local/remove_missing_taxids'
include { RETRIEVE_SEQS       } from '../../modules/local/retrieve_seqs'


workflow PREPARE_MAPPING {

    take:
    classifier_metadata      // params.filtered_hits
    blast_db                 // params.blast_db


    main:
    ch_versions = Channel.empty()

    ch_filtered_hits = Channel.fromPath(classifier_metadata)
                            .splitCsv ( header:true )
                            .map { create_tsv_channel(it) }
    // ch_filtered_hits.dump(tag: "samples")

    ch_blast_db = Channel.fromPath(blast_db)
    // ch_blast_db.dump(tag: "blast_db")
    ch_prep_for_validation = ch_filtered_hits.combine(ch_blast_db)

    // ch_prep_for_validation.dump(tag: "pre_val")
    ch_not_found_taxids = VALIDATE_TAXIDS( ch_prep_for_validation )
    ch_versions = ch_versions.mix(VALIDATE_TAXIDS.out.versions)
    // ch_not_found_taxids[0].dump(tag:'unvalidated')
    ch_excludable = ch_prep_for_validation.combine(ch_not_found_taxids.txt, by:0) //.dump(tag:'combined')
    ch_taxids_validated = REMOVE_MISSING_TAXIDS( ch_excludable )
    ch_versions = ch_versions.mix(REMOVE_MISSING_TAXIDS.out.versions)
    // ch_taxids_validated[0].dump(tag:'validated')

    ch_split = ch_taxids_validated[0]
                        .multiMap { it ->
                                    def new_meta = [:]
                                    new_meta = it[0]
                                    new_meta.remove('path') // Drop unvalidated tsv from meta.
                                    tsv : [new_meta, it[3]] // val(meta), path(validated.tsv)
                                    meta_data: [new_meta, it[1], it[2]] // val(meta), path(fastq), path(blast_db)
                                }
    // ch_split.tsv.dump(tag: "split_meta_tsv")
    // ch_split.meta_data.dump(tag: "split_meta_data")
    ch_parsed = ch_split.tsv.splitCsv( header:true, sep:'\t' )
                                .map{ meta_data, row ->
                                    def meta = [:]
                                    meta.taxon = row.taxon_name
                                    meta.taxid = row.taxid
                                    [meta_data, meta_data + meta]   // Split by rows the tsv and include in meta the taxon name and taxid,
                                                                    // keep the old meta data so that it can be used for joining with the
                                                                    // channel with path(fastq) and path(blast_db).
                                }
                                .combine(ch_split.meta_data, by: 0) // Join path(fastq) and path(blast_db) to the meta data channel
                                .map{ it ->                         // Drop the old meta data since the new one contains same data and even more.
                                    [it[1], it[2], it[3]]           // val(new_meta), path(fastq), path(blast_db)
                                }
    // ch_parsed.dump(tag: "split_parsed")
    ch_ref_genomes = RETRIEVE_SEQS( ch_parsed )
    // ch_ref_genomes.fna.dump(tag: 'ref')
    ch_versions = ch_versions.mix(RETRIEVE_SEQS.out.versions)


    emit:
    fna      = ch_ref_genomes.fna  // channel: [ val(meta), path(fastq), path(blastdb), path('*.fna') ]
    versions = ch_versions         // channel: path(versions.yml)
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
