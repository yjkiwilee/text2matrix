# Install package manager if not installed already
# install.packages("pacman")

# Load necessary packages
pacman::p_load("tidyverse", "here", "jsonlite")

# Load json
# Data from desc2matrix_accum.py, which populates the initial character
# list by asking the prompt from desc2matrix.py with the first species description
accum_dat <- read_json(here("../json_outputs/accum_out_800sp.json"))
# Data from desc2matrix_accum_tab.py, which populates the initial character
# list by asking the LLM to tabulate the characteristics from the first three species descriptions
accum_tab_dat <- read_json(here("../json_outputs/accum_tab_out_800sp.json"))

# ===== Generate accumulation curve =====

# Get charlist length histories
accum_charlen <- c(NA, accum_dat$charlist_len_history) # Insert NA because accum_charlen lacks the 'initial' charlist from tabulation
accum_tab_charlen <- accum_tab_dat$charlist_len_history

# Extend shorter charlen
charlens <- list(accum_charlen, accum_tab_charlen)
max_len <- max(sapply(charlens, length))
charlens_regularised <- lapply(lapply(charlens, unlist), "length<-", max_len)

accum_charlen_reg <- charlens_regularised[[1]]
accum_tab_charlen_reg <- charlens_regularised[[2]]

# Get incidences of failure
accum_failures <- sapply(seq_along(accum_dat$data), function(spdat_id) {
  spdat <- accum_dat$data[[spdat_id]]
  if(spdat$status == "success") { NA }
  else { spdat_id + 1 } # + 1 to account for NA
})
accum_tab_failures <- sapply(seq_along(accum_tab_dat$data), function(spdat_id) {
  spdat <- accum_tab_dat$data[[spdat_id]]
  if(spdat$status == "success") { NA }
  else { spdat_id }
})
fail_df <- tibble(
  fail_sp_i = c(NA, accum_failures), # First is NA, corresponding to the missing initial tabulation
  accum_charlen = as.numeric(accum_charlen)
)
fail_tab_df <- tibble(
  fail_sp_i = c(NA, accum_tab_failures), # First is NA, corresponding to the fact that the initial tabulation can't have failed
  accum_tab_charlen = as.numeric(accum_tab_charlen)
)

# Build tibble
accum_df <- tibble(
  sp_i = seq(0, max_len - 1), # Number of species processed
  accum_charlen = as.numeric(accum_charlen_reg), # Number of characteristics retrieved from accum
  accum_tab_charlen = as.numeric(accum_tab_charlen_reg) # " retrieved from accum_tab
)

# Pivot longer
accum_long_df <- accum_df %>%
  pivot_longer(c(accum_charlen, accum_tab_charlen), names_to = "method", values_to = "charlen") %>%
  mutate(
    method = as.factor(method)
  )

# Rename methods
levels(accum_long_df$method) <- list(accum = "accum_charlen", accum_tab = "accum_tab_charlen")

# Plot accumulation curve
accum_plt <- ggplot() +
  geom_line(data = accum_long_df, aes(x = sp_i, y = charlen, color = method)) +
  geom_point(data = fail_df, aes(x = fail_sp_i, y = accum_charlen), shape = 4) +
  geom_point(data = fail_tab_df, aes(x = fail_sp_i, y = accum_tab_charlen), shape = 4) +
  labs(
    x = "Number of species processed",
    y = "Number of characteristics",
    color = "Method",
  ) +
  scale_color_brewer(palette = "Dark2", labels = c("Without initial tabulation", "With initial tabulation")) +
  theme_bw() +
  theme(legend.position = "bottom")
accum_plt
ggsave(here::here("figures/accum_curve_800.png"), accum_plt, width = 5, height = 4)

# ===== Inspect final trait list for the two runs =====

acc_final_charlist <- accum_dat$charlist_history[[length(accum_dat$charlist_history)]]
paste(unlist(acc_final_charlist), collapse = ", ")
acc_tab_final_charlist <- accum_tab_dat$charlist_history[[length(accum_tab_dat$charlist_history)]]
paste(unlist(acc_tab_final_charlist), collapse = ", ")

# Characters retrieved in both runs
comm <- intersect(acc_final_charlist, acc_tab_final_charlist)
# Characters retrieved only without tabulation
acc_only <- setdiff(acc_final_charlist, acc_tab_final_charlist)
# Characters retrieved only with tabulation
acc_tab_only <- setdiff(acc_tab_final_charlist, acc_final_charlist)

# Make lengths the same
chars_temp_list <- list(comm, acc_only, acc_tab_only)
chars_max_len <- max(sapply(chars_temp_list, length))
chars_temp_reg <- lapply(lapply(chars_temp_list, unlist), "length<-", chars_max_len)

# Generate markdown table string

na_process <- function(val) {
  ifelse(is.na(val), "", val)
}

tab_rows <- sapply(seq(1, chars_max_len), function(i) {
  paste0("| ",
         na_process(chars_temp_reg[[1]][[i]]),
         " | ",
         na_process(chars_temp_reg[[2]][[i]]),
         " | ",
         chars_temp_reg[[3]][[i]],
         " |")
})

rows_str <- paste(tab_rows, collapse = "\n")

tab_str <- paste(c("| Retrieved in both runs | Without tabulation only | With tabulation only |",
                 "| --- | --- | --- |",
                 rows_str),
                 collapse = "\n")
tab_str
