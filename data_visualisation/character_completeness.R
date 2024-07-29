# Load necessary packages
pacman::p_load("tidyverse", "here", "plyr")

# Load json
# Data from desc2matrix_accum.py, which populates the initial character
# list by asking the prompt from desc2matrix.py with the first species description
accum_dat <- read_json(here::here("../json_outputs/accum_out_800sp.json"))
# Data from desc2matrix_accum_tab.py, which populates the initial character
# list by asking the LLM to tabulate the characteristics from the first three species descriptions
accum_tab_dat <- read_json(here::here("../json_outputs/accum_tab_out_800sp.json"))
# Data from desc2matrix_accum_followup.py, which is built upon desc2matrix_accum_tab.py
# but asks a 'follow-up question' including words that were omitted from the original description
# to increase trait coverage
accum_f_dat <- read_json(here::here("../json_outputs/accum_followup_out_800sp.json"))