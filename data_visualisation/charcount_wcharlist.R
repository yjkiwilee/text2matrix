# Install package manager if not installed already
# install.packages("pacman")

# Load necessary packages
pacman::p_load("tidyverse", "here", "jsonlite", "ggVennDiagram", "plotly", "ggwordcloud", "scales")

# Load json
# Data from desc2matrix_wcharlist.py with default settings
wcharlist_dat <- read_json(here::here("../outputs/wcharlist_out_800sp.json"))
# Data from desctmatrix_wcharlist_followup.py with default settings
wcharlist_f_dat <- read_json(here::here("../outputs/wcharlist_followup_out_800sp.json"))

# List containing the data
wcharlist_dats <- list(
  wcharlist = wcharlist_dat,
  wcharlist_f = wcharlist_f_dat
)

# ===== Generate accumulation curve =====

# Get output character list length histories
wcharlist_charlens <- lapply(wcharlist_dats, function(wcharlist_d) {
  lapply(wcharlist_d$data, function(species) {
    if(is.null(species$char_json)) { NA }
    else { as.numeric(length(species$char_json)) }
  })
})

# Get incidences of failures
wcharlist_failures <- lapply(wcharlist_dats, function(wcharlist_d) {
  sapply(seq_along(wcharlist_d$data), function(spdat_id) {
    spdat <- wcharlist_d$data[[spdat_id]]
    if(spdat$status == "success") { NA }
    else { spdat_id }
  })
})

fail_df <- tibble(
  sp_id = do.call(c, wcharlist_failures),
  charlen = do.call(c, unlist(wcharlist_charlens, recursive = FALSE))
)

# Method names
method_names <- c("wcharlist", "wcharlist_f")
method_list <- lapply(seq_along(wcharlist_charlens), function(i) { rep(method_names[i], length(wcharlist_charlens[[i]])) })

# Species IDs
id_list <- lapply(wcharlist_charlens, function(charlens) { seq(1, length.out = length(charlens)) })
sp_ids <- unlist(id_list)

# Build tibble
wcharlist_df <- tibble(
  sp_id = sp_ids, # Number of species processed
  charlen = unlist(wcharlist_charlens), # Number of characteristics retrieved from the runs
  method = unlist(method_list)
)

wcharlist_df

# Plot histogram of the distribution of the length of characteristic list obtained
method_lab <- c("Constant trait list provided", "Constant trait list provided with follow-up question")
names(method_lab) <- c("wcharlist", "wcharlist_f")

wcharlist_plt <- ggplot(wcharlist_df, aes(x = charlen)) +
  geom_vline(xintercept = 89, linetype = "dashed") +
  geom_histogram(binwidth = 5, fill = "#ffffff", color = "#000000", boundary = 0) +
  labs(
    title = "The number of characteristics in the output across successful runs",
    x = "Number of output characteristics",
    y = "Count"
  ) +
  facet_wrap(~ method, ncol = 1, labeller = labeller(method = method_lab), scales = "free_y") +
  theme_bw() +
  theme(legend.position = "bottom") +
  guides(color = guide_legend(nrow = 2, byrow = FALSE))
wcharlist_plt
ggsave(here::here("figures/wcharlist_char_800_followup.png"), wcharlist_plt, width = 5, height = 4)

# ===== Inspect final trait list for the runs =====

# ===== Venn diagram of characteristics =====

# Gather charlist histories
accum_charhist <- list(
  accum_dat$charlist_history,
  accum_lc_dat$charlist_history,
  accum_lf_dat$charlist_history,
  accum_lclf_dat$charlist_history
)

# Extract final charlists
final_chars <- lapply(accum_charhist, function(charhist) {
  final_charlist <- unlist(charhist[[length(charhist)]])
  unname(sapply(final_charlist, function(char) { sub("color", "colour", char, ignore.case = TRUE) })) # Make spelling variants uniform
})
names(final_chars) <- c("accum", "accum_lc", "accum_lf", "accum_lclf")

paste(final_chars[["accum"]], collapse = ", ")
paste(final_chars[["accum_lc"]], collapse = ", ")
paste(final_chars[["accum_lf"]], collapse = ", ")
paste(final_chars[["accum_lclf"]], collapse = ", ")

# Draw Venn diagram of characteristics
char_venn <- ggVennDiagram(final_chars,
                           category.names = c("A", "AT", "AF")) +
  scale_fill_gradient(low = "#ffffff", high = "#333333") +
  labs(
    title = "Venn diagram of final characteristics,\nwith merged spelling variants",
    fill = "Count"
  )
char_venn
ggsave(here::here("figures/characters_venn.png"), char_venn, width = 5, height = 4, bg = "white")

# ===== Venn diagram of words =====

# Decompose to individual words and find shared words
final_chars_words <- lapply(final_chars, function(charlist) {
  words <- unlist(lapply(charlist, function(char) { strsplit(char, " ") }))
})

# Draw Venn diagram of words
char_word_venn <- ggVennDiagram(final_chars_words,
                                category.names = c("A", "AT", "AF")) +
  scale_fill_gradient(low = "#ffffff", high = "#333333") +
  labs(
    title = "Venn diagram of words in the final characteristics,\nwith merged spelling variants",
    fill = "Count"
  )
char_word_venn
ggsave(here::here("figures/characters_words_venn.png"), char_word_venn, width = 5, height = 4, bg = "white")

# ===== Word clouds =====

# Extract word blobs from the trait histories of the runs
char_blobs <- list(
  accum = unlist(accum_dat$charlist_history),
  accum_tab = unlist(accum_tab_dat$charlist_history),
  accum_f = unlist(accum_f_dat$charlist_history)
)

# Separate into words
word_blobs <- lapply(char_blobs, function(char_blob) {
  unlist(lapply(char_blob, function(char) { str_split(char, " ") }))
})

# Count words
word_dfs <- lapply(names(word_blobs), function(blob_name) {
  blob <- word_blobs[[blob_name]]
  word_tab <- sort(table(blob))
  words <- names(word_tab)
  counts <- unlist(word_tab, use.names = FALSE)
  order <- seq(0, length(words) - 1)
  tibble(
    method = factor(rep(blob_name, length(words)), levels = c("accum", "accum_tab", "accum_f")),
    word = words,
    word_count = as.numeric(counts),
    freq_category = as.factor((order / length(words)) %/% (1/3))
  )
})

word_df <- bind_rows(word_dfs)

word_df

# Plot word clouds

facet_labeller <- c("Without tabulation", "With tabulation", "With tabulation & followup")
names(facet_labeller) <- c("accum", "accum_tab", "accum_f")

set.seed(1)
word_cloud <- ggplot(word_df, aes(label = word, size = sqrt(word_count + 50), y = freq_category)) +
  geom_text_wordcloud() +
  scale_size_area(max_size = 7) +
  theme_minimal() +
  facet_wrap(~ method, labeller = labeller(method = facet_labeller)) +
  theme(
    strip.text.x = element_text(size = 8),
    axis.title.y = element_blank(),
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    panel.grid.major=element_blank(),
    panel.grid.minor=element_blank()
  )
word_cloud
ggsave(here::here("figures/word_clouds.png"), word_cloud, width = 8, height = 8, bg = "white")
