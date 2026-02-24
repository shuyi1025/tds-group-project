rm(list = ls())

# load libraries
library(dplyr)

# load data
ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")
ukb_drop <- ukb_v2

vars_base <- c(
  "mh_irritability",
  "mh_loneliness_isolation",
  "mh_miserableness",
  "mh_mood_swings",
  "mh_nervous_feelings",
  "mh_sensitivity",
  "mh_suffer_nerves",
  "mh_tense",
  "mh_worrier",
  "mh_worry_embarrassment",
  "mh_fed_feelings",
  "mh_guilty_feelings"
)

# regex: ^(var1|var2|var3)\.
pattern <- paste0("^(", paste(vars_base, collapse = "|"), ")\\.")

# sanity check what will be dropped
cols <- grep(pattern, names(ukb_drop), value = TRUE)
cat("Number of columns to drop:", length(cols), "\n")
cols

#  drop
ukb_drop <- ukb_drop %>%
  select(-matches(pattern))

# confirm removal
remaining <- grep(pattern, names(ukb_drop), value = TRUE)
cat("Remaining columns after drop:", length(remaining), "\n")
remaining
# should be character(0)


# save cleaned dataset
saveRDS(
  ukb_drop,
  "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds"
)
