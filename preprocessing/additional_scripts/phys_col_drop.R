rm(list = ls())

# load libraries
library(dplyr)

# load data
ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")
ukb_drop <- ukb_v2

pa_vars_base <- c(
  "phys_walk_duration",
  "phys_vigorous_activity_duration",
  "phys_usual_walking_pace",
  "phys_strenuous_sports_freq_last4w",
  "phys_strenuous_sports_duration",
  "phys_mvpa_walking_rec_met",
  "phys_mvpa_rec_met",
  "phys_moderate_activity_duration",
  "phys_light_diy_freq_last4w",
  "phys_light_diy_duration",
  "phys_days_per_week_walked_10plus_min",
  "phys_days_per_week_vigorous_activity_10plus_min",
  "phys_days_per_week_moderate_activity_10plus_min",
  "phys_heavy_diy_freq_last4w",
  "phys_heavy_diy_duration",
  "phys_walking_for_pleasure_duration",
  "phys_walking_for_pleasure_freq_last4w"
)

# regex: ^(var1|var2|var3)\.
pa_pattern <- paste0("^(", paste(pa_vars_base, collapse = "|"), ")\\.")

# sanity check what will be dropped
pa_cols <- grep(pa_pattern, names(ukb_drop), value = TRUE)
cat("Number of columns to drop:", length(pa_cols), "\n")
pa_cols

#  drop
ukb_drop <- ukb_drop %>%
  select(-matches(pa_pattern))

# confirm removal
remaining_pa <- grep(pa_pattern, names(ukb_drop), value = TRUE)
cat("Remaining columns after drop:", length(remaining_pa), "\n")
remaining_pa
# should be character(0)


# save cleaned dataset
saveRDS(
  ukb_drop,
  "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds"
)
