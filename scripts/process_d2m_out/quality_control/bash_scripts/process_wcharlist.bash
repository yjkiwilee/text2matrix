#!/bin/bash

# This script is for running the compare_chars.py script on the wcharlist output files.
cd ..

source ../env/Scripts/activate

python compare_chars.py ../data/output_backup/wcharlist/subset/wcharlist_subset.json ../data/output_backup/solanum_chars/json/solanum_spp.json ../data/solanaceae-taxa-subset.txt ../data/output_backup/compare_chars/subset/wcharlist_comp.tsv

python compare_chars.py ../data/output_backup/wcharlist/subset/wcharlist_sgenlist_subset.json ../data/output_backup/solanum_chars/json/solanum_spp.json ../data/solanaceae-taxa-subset.txt ../data/output_backup/compare_chars/subset/wcharlist_sgenlist_comp.tsv

python compare_chars.py ../data/output_backup/wcharlist/subset/wcharlist_lgenlist_subset.json ../data/output_backup/solanum_chars/json/solanum_spp.json ../data/solanaceae-taxa-subset.txt ../data/output_backup/compare_chars/subset/wcharlist_lgenlist_comp.tsv

python compare_chars.py ../data/output_backup/wcharlist/subset/wcharlist_f_subset.json ../data/output_backup/solanum_chars/json/solanum_spp.json ../data/solanaceae-taxa-subset.txt ../data/output_backup/compare_chars/subset/wcharlist_f_comp.tsv

python compare_chars.py ../data/output_backup/wcharlist/subset/wcharlist_f_sgenlist_subset.json ../data/output_backup/solanum_chars/json/solanum_spp.json ../data/solanaceae-taxa-subset.txt ../data/output_backup/compare_chars/subset/wcharlist_f_sgenlist_comp.tsv

python compare_chars.py ../data/output_backup/wcharlist/subset/wcharlist_f_lgenlist_subset.json ../data/output_backup/solanum_chars/json/solanum_spp.json ../data/solanaceae-taxa-subset.txt ../data/output_backup/compare_chars/subset/wcharlist_f_lgenlist_comp.tsv