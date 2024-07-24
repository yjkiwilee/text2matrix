# Install package manager if not installed already
# install.packages("pacman")

# Load necessary packages
pacman::p_load("tidyverse", "here", "jsonlite")

# Load json
charjson_dat <- read_json(here("accum_out.json"))

# ===== Generate accumulation curve =====

# Get charlist history and charlist length history
charlist_hist <- charjson_dat$charlist_history
charlistlen_hist <- charjson_dat$charlist_len_history

# Build tibble
accum_df <- tibble(
  sp_i = seq(1, length(charlistlen_hist)),
  charlist_len = as.numeric(charlistlen_hist)
)

# Plot accumulation curve
accum_plt <- ggplot(accum_df, aes(x = sp_i, y = charlist_len)) +
  geom_line() +
  theme_bw() +
  scale_y_continuous(limits = c(0, 50))
accum_plt
ggsave(here("figures/accum_curve.png"), accum_plt, width = 4, height = 3)
