# umierrorcorrect

Pipeline for analyzing  barcoded amplicon sequencing data with Unique molecular identifiers (UMI)

Installation
------------

### Alternative a) Run via Docker

If you have Docker installed, pull the Docker image from Docker hub.

```bash
docker pull tobiasosterlund/umierrorcorrect
```

Download a reference genome fasta file and mount the reference directory and data directory (including fastq files) to the docker container:

```bash
docker run -it tobiasosterlund/umierrorcorrect -v /path_to_reference_fasta_directory/:/references/ \\
-v /path_to_data_directory/:/data/
```
To try to run the pipeline:

```bash
run_umierrorcorrect.py -h
cd /data/
```

See below for information about how to run the pipeline and how to index the reference genome with bwa.

### Alternative b) Install from source

To install the UMI-errorcorrect pipeline, open a terminal and type the following:

```bash
wget https://github.com/tobbeost/umierrorcorrect/archive/v0.12.tar.gz
pip install v0.12.tar.gz
```
    
After installation, try to run the pipeline:

```bash
run_umierrorcorrect.py -h
```

Dependencies
------------

Umi-errorcorrect runs using Python and requires the following programs/libraries to be installed (if you run through docker all dependencies are already handled):

Python-libraries (should be installed automatically):

    pysam (v 0.8.4 or greater)

External programs:

    bwa (bwa mem command is used)
    Either of gzip or pigz (parallel gzip)

Install the external programs and add them to the path.

Since the umierrorcorrect pipeline is using `bwa` for mapping of reads, a bwa-indexed reference genome is needed. Index the reference genome with the command `bwa index -a bwtsw reference.fa`.

Usage
-----

Example syntax for running the whole pipeline:

    run_umierrorcorrect.py -r1 read1.fastq.gz -r2 read2.fastq.gz -ul umi_length -sl spacer_length -r reference_fasta_file.fasta -o output_directory

The ``run_umierrorcorrect.py`` pipeline performs the following steps:

- Preprocessing of fastq files (remove the UMI and spacer and puts the UMI in the header)
- Mapping of preprocessed fastq reads to the reference genome
- Perform UMI clustering, then error correcion of each UMI cluster
- Create consensus reads (one representative read per UMI cluster written to a BAM file)
- Create a consensus output file (collapsed counts per position)

It is also to possible to run the pipeline step-by-step.

To see the options for each step, type the following:

```bash
preprocess.py -h
run_mapping.py -h
umi_error_correct.py -h
get_consensus_statistics.py -h
filter_bam.py -h
filter_cons.py -h
```
Tutorial
--------

[Link to the Umierrorcorrect tutorial](https://github.com/tobbeost/umierrorcorrect/wiki/Tutorial)


Example of UMI definition options
----------------------------------

[UMI definition options](https://github.com/tobbeost/umierrorcorrect/wiki/UMI-definition-options)
