#!/usr/bin/env python3

import sys
import pickle
import pysam
from testgroup3 import umi_cluster

def get_consensus(bamfilename,umis,family_sizes):
    consensus_sequence={}
    for fs in family_sizes:
        consensus_sequence[fs]={}
    position_matrix={}
    with pysam.AlignmentFile(bamfilename,'rb') as f:
        alignment=f.pileup('17',7577497,7577615,max_depth=1000000)
        n=0
        clustlist=['GCACCCGCGCCC','GCACCCGCGCAC','GCACCCGGGCCC']
        for pileupcolumn in alignment:
            pos=pileupcolumn.pos
            #print(pos)
            for read in pileupcolumn.pileups:
                barcode=read.alignment.qname.split(':')[-1]
                if barcode in clustlist and pos==7577513:
                    n+=1
                cluster=umis[barcode].centroid
                cluster_size=umis[barcode].count
                    
                if not read.is_del and not read.indel:
                    allele=read.alignment.query_sequence[read.query_position]
                    #if cluster in 'GCACCCGCGCCC' and pos==7577497:
                    #    print(allele)
                    #    n+=1
                else:
                    allele='D'
                if cluster not in position_matrix:
                    position_matrix[cluster]={}
                if pos not in position_matrix[cluster]:
                    position_matrix[cluster][pos]={}
                if allele not in position_matrix[cluster][pos]:
                    position_matrix[cluster][pos][allele]=0
                position_matrix[cluster][pos][allele]+=1
    print(n)
    return(position_matrix)



def main(bamfilename):
    with open('/home/xsteto/umierrorcorrect/umi.pickle','rb') as f:
        umis=pickle.load(f)
    family_sizes=[0,1,2,3,4,5,7,10,20,30]
    
    position_matrix=get_consensus(bamfilename,umis,family_sizes)
    print(position_matrix['GCACCCGCGCCC'])
    print(len(position_matrix))
    #print(position_matrix['GCACCCGCGCAC'])
    #print(position_matrix['GCACCCGGGCCC'])
if __name__=='__main__':
    main(sys.argv[1])
