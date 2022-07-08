#!/usr/bin/env python
"""Parse the samplesheet into dataframes."""

# Load packages
import os
import argparse
import pandas as pd
from sys import argv
import csv


input_file = argv[1]
if input_file.endswith('.csv'):
## Read the kraken file into dataframe
    kraken_df = pd.read_csv (input_file).iloc[:,1].values[0]
    centrifuge_df = pd.read_csv (input_file).iloc[:,2]

    print(kraken_df)
with open(kraken_df, 'r') as rf:
    reader = csv.reader(rf, delimiter="\t")
    for row in reader:
      print (row)

#parser = argparse.ArgumentParser(description='Parse the samplesheet into dataframes.')
#parser.add_argument('--samplesheet',
#                    metavar='samplesheet',
#                    help='Path to different classifiers in the samplesheet.')

#args = parser.parse_args()

#kraken_classification = os.path.join(
#    args.samplesheet,
#    'assets',
#    'tsvs',
#    'Viruspool_pe-Viruspool-kraken2.kraken2.report.tsv'
#)
##centrifuge_classification = os.path.join(
#    args.samplesheet,
#    'assets',
#    'tsvs',
#    'Viruspool_pe-Viruspool.centrifuge.tsv'
#)

#kraken_report = pd.read_csv(kraken_classification,
#                    header=None, sep='\t')
#print(kraken_report)
