#!/usr/bin/env python3
'''
UMI error correct, preprocess.py - remove UMI and append to the header of Fastq sequences.
================================

:Author: Tobias Österlund

Purpose
-------

Preprocess the fastq files by removing the unique molecular index and add it to the header of the fastq entry.

'''
import sys
import gzip
from umierrorcorrect.src.handle_sequences import read_fastq, read_fastq_paired_end
import argparse
import os
import logging
import subprocess


def parseArgs():
    parser = argparse.ArgumentParser(description="Pipeline for analyzing  barcoded amplicon sequencing data with Unique molecular identifiers (UMI)")
    parser.add_argument('-o', '--output_path', dest='output_path', help='Path to the output directory, required', required=True)
    parser.add_argument('-r1', '--read1', dest='read1', help='Path to first FASTQ file, R1, required', required=True)
    parser.add_argument('-r2', '--read2', dest='read2', help='Path to second FASTQ file, R2 if applicable')
    parser.add_argument('-ul', '--umi_length', dest='umi_length', help='Length of UMI sequence (number of nucleotides). The UMI is assumed to be located at the start of the read. Required', required=True)
    parser.add_argument('-sl', '--spacer_length', dest='spacer_length', help='Length of spacer (The number of nucleotides between the UMI and the beginning of the read). The UMI + spacer will be trimmed off, and the spacer will be discarded. Default=%(default)s', default='0')
    parser.add_argument('-mode', '--mode', dest='mode', help="Name of library prep, Either 'single' or 'paired', for single end or paired end data respectively, [default = %(default)s]", default="paired")
    parser.add_argument('-dual', '--dual_index', dest='dual_index', help='Include this flag if dual indices are used (UMIs both on R1 and R2)', action='store_true')
    parser.add_argument('-reverse', '--reverse_index', dest='reverse_index', help="Include this flag if a single index (UMI) is used, but the UMI is located on R2 (reverse read). Default is UMI on R1.", action='store_true')
    parser.add_argument('-tmpdir', '--tmp_dir', dest='tmpdir', help="temp directory where the temporary files are written and then removed. Should be the scratch directory on the node. Default is a temp directory in the output folder.")
    parser.add_argument('-cs', '--chunk_size', dest='chunksize', help="Chunk size for reading the fastq files in chunks. Only used if num_threads > 1. [default = %(default)i]", default=25000)
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


def generate_random_dir(tmpdir):
    '''Generate a directory for storing temporary files, using a timestamp.'''
    import datetime
    newtmpdir = tmpdir + '/r' + datetime.datetime.now().strftime("%y%m%d_%H%M%S") + '/'
    newtmpdir = check_output_directory(newtmpdir)
    return(newtmpdir)


def run_unpigz(filename, tmpdir, num_threads):
    '''Unzip the fastq.gz files using parallel gzip (pigz).'''
    outfilename = tmpdir + '/' + filename.split('/')[-1].rstrip('.gz')
    command = ['unpigz', '-p',  num_threads, '-c', filename]
    with open(outfilename, 'w') as g:
        p = subprocess.Popen(command, stdout=g)
        p.communicate()
    return(outfilename)


def run_pigz(filename, num_threads):
    '''Zip the new fastq files with parallel gzip (pigz).'''
    command = ['pigz', '-p', num_threads, filename]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()


def get_sample_name(read1, mode):
    '''Get the sample name as the basename of the input files.'''
    if mode == 'single':
        samplename = read1.split('/')[-1].rstrip('fastq').rstrip('fastq.gz')
    elif mode == 'paired':
        samplename = read1.split('/')[-1].rstrip('fastq').rstrip('fastq.gz').rstrip('_R012')
    return(samplename)


def chunks_paired(read1, read2, chunksize, tmpdir):
    '''Read the fastq files in chunks. Not used in the current pipeline.'''
    fid = 1
    name_list = []
    with open(read1, 'r') as infile1, open(read2, 'r') as infile2:
        chunkname = tmpdir + '/' + 'chunk%d' % fid
        print(chunkname)
        print(chunksize)
        f1 = open(chunkname+'_1.fastq', 'w')
        f2 = open(chunkname+'_2.fastq', 'w')

        for i, (a, b) in enumerate(zip(infile1, infile2)):
            f1.write(a)
            f2.write(b)

            if not (i+2) % (chunksize*4) and not i == 0:
                f1.close()
                f2.close()
                name_list.append(chunkname+'_1.fastq')
                fid += 1
                chunkname = tmpdir + '/chunk%d' % fid
                f1 = open(chunkname + '_1.fastq', 'w')
                f2 = open(chunkname + '_2.fastq', 'w')
        name_list.append((chunkname + '_1.fastq', chunkname + '_2.fastq'))
        f1.close()
        f2.close()
    return name_list
#
#
# def trim_barcode(sequence, barcode_length, spacer_length):
#    '''Trim the barcode and spacer from a sequence and return the barcode and rest of the sequence.'''
#    barcode = sequence[:barcode_length]
#    # spacer=sequence[barcode_length:barcode_length+spacer_length]
#    rest = sequence[barcode_length+spacer_length:]
#    return((barcode, rest))


def preprocess_se(infilename, outfilename, barcode_length, spacer_length):
    '''Run the preprocessing for single end data (one fastq file).'''
    try:
        barcode_length = int(barcode_length)
    except ValueError as e:
        logging.warning(e + " Barcode length needs to be an integer")
        sys.exit(1)
    try:
        spacer_length = int(spacer_length)
    except ValueError as e:
        logging.warning(e + " Spacer length needs to be an integer")
        sys.exit(1)
    print(infilename,outfilename)
    with open(infilename) as f, open(outfilename, 'w') as g:
        read_start = barcode_length + spacer_length
        for name, seq, qual in read_fastq(f):
            barcode = seq[:barcode_length]
            # g.write(name+':'+barcode+'\n'+rest+'\n'+qualname+'\n'+qual[12+11:]+'\n')
            parts = name.split()
            newname = ':'.join([parts[0], barcode]) + ' ' + parts[-1]
            g.write('\n'.join([newname, seq[read_start:], '+', qual[read_start:]]) + '\n')


def preprocess_pe(r1file, r2file, outfile1, outfile2, barcode_length, spacer_length, dual_index):
    '''Run the preprocessing for paired end data (two fastq files).'''
    try:
        barcode_length = int(barcode_length)
    except ValueError as e:
        logging.warning(e + " Barcode length needs to be an integer")
        sys.exit(1)
    try:
        spacer_length = int(spacer_length)
    except ValueError as e:
        logging.warning(e + " Spacer length needs to be an integer")
        sys.exit(1)
    print(r1file, r2file)
    read_start = barcode_length + spacer_length
    with open(r1file) as f1, open(r2file) as f2, open(outfile1, 'w') as g1, open(outfile2, 'w') as g2:
        for name1, seq1, qual1, name2, seq2, qual2 in read_fastq_paired_end(f1, f2):
            if dual_index:
                barcode = seq1[:barcode_length] + seq2[:barcode_length]
            else:
                barcode = seq1[:barcode_length]
            parts1 = name1.split()
            parts2 = name2.split()
            newname1 = ':'.join([parts1[0], barcode]) + ' ' + parts1[-1]
            newname2 = ':'.join([parts2[0], barcode]) + ' ' + parts2[-1]
            g1.write('\n'.join([newname1, seq1[read_start:], '+', qual1[read_start:]]) + '\n')
            if dual_index:
                g2.write('\n'.join([newname2, seq2[read_start:], '+', qual2[read_start:]]) + '\n')
            else:
                g2.write('\n'.join([newname2, seq2, '+', qual2]) + '\n')


def run_preprocessing(args):
    '''Start preprocessing.'''
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
    logging.info('Starting UMI Error Correct')
    args.output_path = check_output_directory(args.output_path)  # check if output path exists
    if args.mode == 'paired':
        if not args.read2:
            logging.warning("R1 and R2 Fastq files are required for mode 'paired', exiting.")
            sys.exit(1)
    if args.tmpdir:
        newtmpdir = generate_random_dir(args.tmpdir)
    else:
        newtmpdir = generate_random_dir(args.output_path)
    # args.chunksize=int(args.chunksize)
    # Unzip the fastq.gz files
    if args.mode == 'paired':
        r1file = run_unpigz(args.read1, newtmpdir, args.num_threads)
        r2file = run_unpigz(args.read2, newtmpdir, args.num_threads)
    else:
        r1file = run_unpigz(args.read1, newtmpdir, args.num_threads)

    logging.info('Writing output files to {}'.format(args.output_path))
    samplename = get_sample_name(args.read1, args.mode)
    if args.mode == 'single':
        outfilename = args.output_path + '/' + samplename + '.fastq'
        #print(r1file)
        #print(outfilename)
        preprocess_se(r1file, outfilename, args.umi_length, args.spacer_length)
        run_pigz(outfilename, args.num_threads)
        os.remove(r1file)
        os.rmdir(newtmpdir)
        fastqfiles=[outfilename + '.gz']
    else:
        if args.reverse_index:
            # switch forward and reverse read
            r1filetmp = r1file
            r1file = r2file
            r2file = r1filetmp
            outfile1 = args.output_path + '/' + samplename + '_R2.fastq'
            outfile2 = args.output_path + '/' + samplename + '_R1.fastq'
        else:
            # r1file=args.read1
            # r2file=args.read2
            outfile1 = args.output_path + '/' + samplename + '_R1.fastq'
            outfile2 = args.output_path + '/'+samplename + '_R2.fastq'
        preprocess_pe(r1file, r2file, outfile1, outfile2, args.umi_length, args.spacer_length, args.dual_index)
        run_pigz(outfile1, args.num_threads)
        run_pigz(outfile2, args.num_threads)
        os.remove(r1file)
        os.remove(r2file)
        os.rmdir(newtmpdir)
        fastqfiles=[outfile1 + '.gz', outfile2 + '.gz']
    return(fastqfiles)

def main(args):
    fastqfiles=run_preprocessing(args)


if __name__ == '__main__':
    args = parseArgs()
    main(args)