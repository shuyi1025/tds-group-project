rm(list = ls())

# load libraries
library(dplyr)

# load data
ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")
ukb_drop <- ukb_v2

env_vars_base <- c(
  "env_greenspace_pct_buffer_1000m",
  "env_domestic_garden_pct_buffer_1000m"
)

# regex: ^(var1|var2|var3)\.
env_pattern <- paste0("^(", paste(env_vars_base, collapse = "|"), ")\\.")

# sanity check what will be dropped
env_cols <- grep(env_pattern, names(ukb_drop), value = TRUE)
cat("Number of columns to drop:", length(env_cols), "\n")
env_cols

#  drop
ukb_drop <- ukb_drop %>%
  select(-matches(env_pattern))

# confirm removal
remaining_env <- grep(pa_pattern, names(ukb_drop), value = TRUE)
cat("Remaining columns after drop:", length(remaining_env), "\n")
remaining_env
# should be character(0)


# save cleaned dataset
saveRDS(
  ukb_drop,
  "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds"
)