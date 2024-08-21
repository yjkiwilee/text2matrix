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
  "wcharlist_sgenlist",
  "wcharlist_lgenlist",
  "wcharlist_f",
  "wcharlist_f_sgenlist",
  "wcharlist_f_lgenlist"
)
names(run_names) <- run_names

# Run labels
run_labels <- c(
  "Characteristics in key",
  "Short list of characteristics extracted by LLM",
  "Long list of characteristics extracted by LLM",
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
    mutate(
      run_name = run_name, # Append column indicating run name
      status = factor(status, levels = c("success", "invalid_json", "invalid_json_followup"))
    ) 
})

# Bind into single dataframe
runs_df <- bind_rows(run_dfs)

# ===== Run status plots =====

status_barplot <- ggplot(runs_df, aes(y = run_name, fill = status)) +
  geom_bar(width = .5) +
  scale_y_discrete(
    labels = run_labels
  ) +
  scale_x_continuous(
    breaks = seq(0, 500, 100)
  ) +
  scale_fill_manual(
    labels = c("Success", "Invalid JSON output in initial prompt", "Invalid JSON output in follow-up prompt"),
    values = c("#abf2a7", "#facc16", "#ed1c09"),
    breaks = c("success", "invalid_json", "invalid_json_followup")
  ) +
  labs(
    x = "Run",
    y = "Count",
    fill = "Status"
  ) +
  theme_classic() +
  theme(
    legend.position = "bottom",
    panel.grid.major.y = element_line(color = "lightgrey", linewidth = 0.5),
    panel.grid.minor.y = element_line(color = "lightgrey", linewidth = 0.25)
  ) +
  guides(fill = guide_legend(ncol=1,byrow=TRUE))

status_barplot
ggsave(here::here("../../script_output/visualise_d2m_out/poster/status.png"), status_barplot, width = 4, height = 5)
