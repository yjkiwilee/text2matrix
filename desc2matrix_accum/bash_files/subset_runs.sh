#!/bin/bash

# This script is for running desc2matrix on the descriptions
# that were subsetting to only include those within the Solanum Key: https://app.xper3.fr/xper3GeneratedFiles/publish/identification/-3915026624309343770/mkey.html

# Go to main branch directory
cd ..
# Activate venv
source ../env/Scripts/activate
# Run desc2matrix_accum scripts
python desc2matrix_accum.py ../data/solanaceae-desc-subset.txt outputs/accum_output/accum_subset.json --desctype=general
python desc2matrix_accum_tab.py ../data/solanaceae-desc-subset.txt outputs/accum_output/accum_tab_subset.json --desctype=general
python desc2matrix_accum_followup.py ../data/solanaceae-desc-subset.txt outputs/accum_output/accum_f_subset.json --desctype=general
# Run desc2matrix_wcharlist scripts
# python desc2matrix_wcharlist.py ../data/solanaceae-desc-subset.txt charlists/solanum_charlist.txt outputs/wcharlist_output/wcharlist_subset.json --desctype=general --prompt=alternative_prompts/prompt_withoutexample.txt --charlistsep="; "
# python desc2matrix_wcharlist_followup.py ../data/solanaceae-desc-subset.txt charlists/solanum_charlist.txt outputs/wcharlist_output/wcharlist_f_subset.json --desctype=general --charlistsep="; "
# Deactivate venv
deactivate
# Exit shell
exit