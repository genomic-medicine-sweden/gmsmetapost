#!/usr/bin/env nextflow

// import modules
include { VALIDATE_TAXIDS        } from '../../modules/local/validate_taxids'
include { REMOVE_MISSING_TAXIDS  } from '../../modules/local/remove_missing_taxids'
include { DOWNLOAD_GENOMES       } from '../../modules/local/download_genomes'
include { ADD_METADATA           } from '../../modules/local/add_metadata'


workflow PREPARE_MAPPING {

    take:
    classifier_results      // params.filtered_hits


    main:
    ch_versions = Channel.empty()

    ch_filtered_hits = Channel.fromPath(classifier_results)
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
    ch_metadata_added = ADD_METADATA( ch_taxids_validated.tsv )
    ch_versions = ch_versions.mix(ADD_METADATA.out.versions)
    // ch_metadata_added[0].dump(tag:'meta_data_added')

    ch_split = ch_metadata_added[0].splitCsv( header:true, sep:'\t' )
                            .map { row ->
                                    def meta = [:]
                                    meta.sample    = row.sample_name[1]
                                    meta.pairing   = row.pairing[1]
                                    meta.taxon     = row.taxon_name[1]
                                    meta.taxid     = row.taxid[1]
                                    meta
                                }

    ch_ref_genomes = DOWNLOAD_GENOMES( ch_split )
    // ch_ref_genomes[0].dump(tag: 'ref')
    ch_versions = ch_versions.mix(DOWNLOAD_GENOMES.out.versions)


    emit:
    tsv = DOWNLOAD_GENOMES.out.fna    // channel: [ val(meta), [ hits ] ]
    versions = ch_versions            // channel: [ versions.yml ]
}

// Function to get list of [ meta, [ kraken2, centrifuge, kaiju ] ]
def create_tsv_channel(LinkedHashMap row) {
    // create meta map
    def meta = [:]
    meta.sample    = row.sample
    meta.pairing   = row.pairing

    def array = []
    if (!file(row.path).exists()) {
        exit 1, "ERROR: Please check input sheet -> classification results file does not exist!\n${row.path}"
    }
    array = [ meta, file(row.path) ]
    return array
}
