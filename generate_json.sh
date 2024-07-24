#!/bin/bash
source env/Scripts/activate
python desc2matrix_accum.py data/solanaceae-desc.txt json_outputs/accum_out.json --desctype=general --spnum=100 
python desc2matrix_accum_tab.py data/solanaceae-desc.txt json_outputs/accum_tab_out.json --desctype=general --spnum=100
deactivate