#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import pysam

def parseArgs():
    parser = argparse.ArgumentParser(description="Pipeline for analyzing  barcoded amplicon sequencing data with Unique molecular identifiers (UMI)")
    parser.add_argument('-o', '--output_path', dest='output_path', help='Path to the output directory, required', required=True)
    parser.add_argument('-r1', '--read1', dest='read1', help='Path to first FASTQ file, R1, required', required=True)
    parser.add_argument('-r2', '--read2', dest='read2', help='Path to second FASTQ file, R2 if applicable')
    parser.add_argument('-r', '--reference', dest='reference_file', help='Path to the reference sequence in Fasta format (indexed), Used for annotation')
    parser.add_argument('-t', '--num_threads', dest='num_threads', help='Number of threads to run the program on. Default=%(default)s', default='1')
    args = parser.parse_args(sys.argv[1:])
    return(args)


def check_output_directory(outdir):
    '''Check if outdir exists, otherwise create it'''
    if os.path.isdir(outdir):
        return(outdir)
    else:
        os.mkdir(outdir)
        return(outdir)


def run_mapping(num_threads, reference_file, fastq_files, output_path):
    '''Run mapping with bwa to create a SAM file, then convert it to BAM, sort and index the file.'''
    output_file = output_path+'/output'
    if len(fastq_files) == 1:
        bwacommand = ['bwa', 'mem', '-t', num_threads, reference_file, fastq_files[0]]
    if len(fastq_files) == 2:
        bwacommand = ['bwa', 'mem', '-t', num_threads, reference_file, fastq_files[0], fastq_files[1]]
    
    with open(output_file + '.sam', 'w') as g:
        p1 = subprocess.Popen(bwacommand, stdout=g)
    p1.communicate()
    p1.wait()
    pysam.view('-Sb', '-@', num_threads,  output_file + '.sam', '-o', output_file + '.bam', catch_stdout=False)
    
    pysam.sort('-@',  num_threads, output_file + '.bam', '-o', output_file + '.sorted.bam', catch_stdout=False)
    pysam.index(output_file + '.sorted.bam', catch_stdout=False)
    os.remove(output_file + '.sam')
    os.remove(output_file + '.bam')
    return(output_file + '.sorted.bam')


if __name__ == '__main__':
    args = parseArgs()
    args.output_path = check_output_directory(args.output_path)
    if args.read2 is None:
        fastq_files = [args.read1]
    else:
        fastq_files = [args.read1, args.read2]

    bamfile=run_mapping(args.num_threads, args.reference_file, fastq_files, args.output_path)
    print(bamfile)
