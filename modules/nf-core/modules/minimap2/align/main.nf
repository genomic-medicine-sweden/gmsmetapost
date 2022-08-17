process MINIMAP2_ALIGN {
    tag "${meta.sample}: ${meta.taxid}"
    label 'process_medium'

    conda (params.enable_conda ? 'bioconda::minimap2=2.21 bioconda::samtools=1.12' : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/mulled-v2-66534bcbb7031a148b13e2ad42583020b9cd25c4:1679e915ddb9d6b4abda91880c4b48857d471bd8-0' :
        'quay.io/biocontainers/mulled-v2-66534bcbb7031a148b13e2ad42583020b9cd25c4:1679e915ddb9d6b4abda91880c4b48857d471bd8-0' }"

    input:
    tuple val(meta), path(reads)
    path reference
    val bam_format
    val cigar_paf_format
    val cigar_bam

    output:
    tuple val(meta), path("*.paf"), optional: true, emit: paf
    tuple val(meta), path("*.bam"), optional: true, emit: bam
    path "versions.yml"           , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.sample}_${meta.taxid}"
    def input_reads = meta.pairing == "single_end" ? "$reads" : "${reads[0]} ${reads[1]}"
    def bam_output = bam_format ? "-a | samtools sort | samtools view -@ ${task.cpus} -b -h -o ${prefix}.bam" : "-o ${prefix}.paf"
    def cigar_paf = cigar_paf_format && !bam_format ? "-c" : ''
    def set_cigar_bam = cigar_bam && bam_format ? "-L" : ''
    """
    minimap2 \\
        $args \\
        -t $task.cpus \\
        $reference \\
        $input_reads \\
        $cigar_paf \\
        $set_cigar_bam \\
        $bam_output

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        minimap2: \$(minimap2 --version 2>&1)
    END_VERSIONS
    """
}
