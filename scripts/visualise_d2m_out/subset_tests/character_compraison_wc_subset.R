# This script visualises the tsv output from process_d2m_out/quality_control/compare_chars.py,
# which compares the characteristics and value output from desc2matrix scripts against their
# counterpart in a structured key of Solanum species, found here:
# https://url.uk.m.mimecastprotect.com/s/YP9XCWQRPfDXo1NIKijuVb2y7

# Load necessary packages
pacman::p_load("tidyverse", "here", "plyr")

# ===== Load tsvs =====

# Run names
run_names <- c(
  "wcharlist",
  "wcharlist_f"
)
names(run_names) <- run_names

# Run labels
run_labels <- c(
  "Without follow-up questions",
  "With follow-up questions"
)

# File paths
tsv_paths <- lapply(run_names, function(run_name) {
  paste0("../../script_output/process_d2m_out/quality_control/compare_chars/", run_name, "_comp.tsv")
})

# Import files
run_dfs <- lapply(seq_along(tsv_paths), function(i) {
  tsv_path <- tsv_paths[[i]]
  run_name <- names(tsv_paths)[[i]]
  read_tsv(here::here(tsv_path)) %>%
    select(-1) %>% # Remove first column
    mutate(run_name = run_name) # Append column indicating run name
})

# Bind into single dataframe
runs_df <- bind_rows(run_dfs)

# ===== Run status plots =====

status_barplot <- ggplot(runs_df, aes(y = run_name, fill = status)) +
  geom_bar()

status_barplot

