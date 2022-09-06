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
                            .map { create_fastq_channel(it) }
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

// Function to create path to fastq files corresponding classifier tsv file
// the function assumes that the classifier tsv file is named e.g.:
// assets/SRR12875558_se-SRR12875558.tsv or e.g.
// assets/SRR12875570_pe-SRR12875570.tsv
def create_path(String accession_id, boolean single_end, String assets_path = "assets/"){
    def path = ""
    if (single_end){
        path = assets_path + accession_id + "_se-" + accession_id + ".tsv"
    } else {
        path = assets_path + accession_id + "_pe-" + accession_id + ".tsv"
    }
    return file(path)
}

// Function to get list of [ meta, [ fastq_1, fastq_2 ] ]
def create_fastq_channel(LinkedHashMap row) {
    // create meta map
    def meta = [:]
    meta.sample                 = row.sample
    meta.instrument_platform    = row.instrument_platform

    def run_accession = row.run_accession
    def fastq_meta = []

    if (meta.instrument_platform == 'OXFORD_NANOPORE') {
        if (row.fastq_2 != '') {
            exit 1, "ERROR: Please check input samplesheet -> For 'instrument_platform' OXFORD_NANOPORE Read 2 FastQ should be empty!\n${row.fastq_2}"
        }
        meta.pairing = "single_end"
        meta.path    = create_path(run_accession, true)
        fastq_meta   = [ meta, [ file(row.fastq_1) ] ]
        return fastq_meta
    } else if (meta.instrument_platform == 'ILLUMINA') {
        if (row.fastq_2 == '') {
            exit 1, "ERROR: Please check input samplesheet -> For 'instrument_platform' ILLUMINA Read 2 FastQ should not be empty!\n${row.fastq_2}"
        }
        if (!file(row.fastq_2).exists()) {
                exit 1, "ERROR: Please check input samplesheet -> Read 2 FastQ file does not exist!\n${row.fastq_2}"
        }
        meta.pairing = "paired_end"
        meta.path    = create_path(run_accession, false)
        fastq_meta   = [ meta, [ file(row.fastq_1), file(row.fastq_2) ] ]
        return fastq_meta
    } else {
        exit 1, "ERROR: Please check input sheet -> 'instrument_platform' value doesn't seem to be one of 'OXFORD_NANOPORE' or 'ILLUMINA'!\n${row.instrument_platform}"
    }
}
