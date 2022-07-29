#!/usr/bin/env python
"""Parse the samplesheet into dataframes."""

# Load packages
import os
import argparse
import pandas as pd
from sys import argv
import csv

def read_kraken_file(file_handle):
    kraken_reader = pd.read_csv(file_handle, delimiter="\t", header=None)

    kraken_reader.columns = ['reads_percentage','#reads_covered','#reads_assigned','rank_code','taxid','scientific_name']
## Calculate the total number of reads being found in the first two rows of second column
    kraken_reader['Total_number_of_reads'] = kraken_reader.loc[0:1,['#reads_covered']].sum(axis=1).cumsum()
## Filter on species and strains
    kraken_reader_rank = kraken_reader[kraken_reader['rank_code'].str.match('S')].iloc[:, :-1]
    total_kraken_reads = kraken_reader.iloc[1][6]
    kraken_reader_rank['RPM'] = kraken_reader_rank.apply(lambda row: row["#reads_assigned"] * 1000000 / total_kraken_reads, axis=1)
    kraken_reader_rank=kraken_reader_rank.sort_values(by=['RPM'], ascending=False)
    kraken_reader_rank.to_csv("kraken_filtered", sep='\t', encoding='utf-8')

##Test code, samplesheet as input
input_file = argv[1]
with open(input_file, 'r') as samplesheet:
    samplesheet_reader = csv.reader(samplesheet)
    #Ignore the header
    next(samplesheet_reader)
    #read_kraken_file(samplesheet_reader)
    for columns in samplesheet_reader:
        for row in columns:
            if "kraken" in row:
                read_kraken_file(row)



#input_file = argv[1]
#if input_file.endswith('.csv'):
## Parse the samplesheet columns
#    kraken_df = pd.read_csv (input_file).iloc[:,1].values[0]
#    centrifuge_df = pd.read_csv (input_file).iloc[:,2].values[0]

