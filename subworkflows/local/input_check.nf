//
// Check input samplesheet and get read channels
//

include { SAMPLESHEET_CHECK } from '../../modules/local/samplesheet_check'

workflow INPUT_CHECK {
    take:
    samplesheet // file: /path/to/samplesheet.csv

    main:
    SAMPLESHEET_CHECK ( samplesheet )
        .csv
        .splitCsv ( header:true, sep:',' )
        .map { create_tsv_channel(it) }
        .set { hits }

    emit:
    hits                                     // channel: [ val(meta), [ hits ] ]
    versions = SAMPLESHEET_CHECK.out.versions // channel: [ versions.yml ]
}

// Function to get list of [ meta, [ kraken2, centrifuge ] ]
def create_tsv_channel(LinkedHashMap row) {
    // create meta map
    def meta = [:]
    meta.id         = row.sample

def array = []
    if (!file(row.kraken2).exists()) {
        exit 1, "ERROR: Please check input samplesheet -> kraken2 classification file does not exist!\n${row.kraken2}"
    }
    if (!file(row.centrifuge).exists()) {
        exit 1, "ERROR: Please check input samplesheet -> centrifuge classification file does not exist!\n${row.centrifuge}"
    }
    array = [ meta,
        file(row.kraken2), file(row.centrifuge)
    ]
    return array


}
