#!/bin/bash

# This script is for running desc2matrix on the descriptions
# that were subsetting to only include those within the Solanum Key: https://app.xper3.fr/xper3GeneratedFiles/publish/identification/-3915026624309343770/mkey.html

# Go to main branch directory
cd ..
# Activate venv
# source ../env/Scripts/activate

python desc2matrix_langchain_wcharlist.py ../data/solanaceae-desc-subset.txt charlists/solanum_charlist.txt outputs/wcharlist_output/wcharlist_langchain_subset.json --desctype=general --charlistsep="; "

python desc2matrix_langchain_wcharlist.py ../data/solanaceae-desc-subset.txt charlists/solanum_charlist_gen_shorter.txt outputs/wcharlist_output/wcharlist_langchain_sgenlist_subset.json --desctype=general --charlistsep="; "

python desc2matrix_langchain_wcharlist.py ../data/solanaceae-desc-subset.txt charlists/solanum_charlist_gen_longer.txt outputs/wcharlist_output/wcharlist_langchain_lgenlist_subset.json --desctype=general --charlistsep="; "

# Deactivate venv
# deactivate