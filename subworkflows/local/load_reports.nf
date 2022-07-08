//
// Parse samplesheet into dataframes
//

include { SAMPLESHEET_PARSE} from '../../modules/local/samplesheet_parse'

workflow LOAD_REPORTS {
    take:
    hits // file: /path/to/samplesheet.csv

    main:
    SAMPLESHEET_PARSE ( hits )
        .csv
        .set { reports }

    emit:
    reports                                     // channel: [ val(meta), [ hits ] ]

    }

// Function to get list of [ meta, [ kraken2, centrifuge ] ]
def create_tsv_channel(LinkedHashMap row) {
    // create meta map
    def meta = [:]
    meta.id = row.sample
    meta.kraken2 = row.kraken2
    meta.centrifuge = row.centrifuge

    def array = []
    array = [ meta,
        file(row.kraken2), file(row.centrifuge)
    ]
    return array


}
