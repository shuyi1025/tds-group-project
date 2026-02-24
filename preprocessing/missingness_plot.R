rm(list = ls())
library(dplyr)
library(tidyr)
library(stringr)

ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")

# ---- 0) prefixes ----
prefixes <- c(
  "sleep", "alc", "diet", "smoke", "phys", "sed",
  "ses", "qualification", "ethnicity",
  "mh",
  "env", "domestic_garden", "employment",
  "sbp", "sex", "yob", "waist_circ", "waist", "mob", "hip_circ", "hip", "fvc", "fev1", "fev_avg",
  "menopause", "cvd", "dob",
  "dx_diabetes", "dbp", "date_recr", "date_lost_to_fup", "bmi",
  "assessment_centre_location", "age_recr", "date_death", "had_menopause", "preg",
  "blood", "biochem",
  "med"
)

# ---- 1) keep cols by prefix ----
all_cols <- colnames(ukb_v2)

cols_keep <- all_cols[
  sapply(all_cols, function(nm) any(str_starts(nm, prefixes)))
]

cols_not_kept <- setdiff(all_cols, cols_keep)

cat("Total vars:", length(all_cols), "\n")
cat("Kept vars :", length(cols_keep), "\n")
cat("Not kept :", length(cols_not_kept), "\n\n")

cat("---- Variables NOT kept ----\n")
print(cols_not_kept)

ukb_subset <- ukb_v2 %>% select(all_of(cols_keep))

# Optional: exclude ID from missingness summaries
if ("eid" %in% names(ukb_subset)) ukb_subset <- ukb_subset %>% select(-eid)

# ---- 2) % missing per variable + domain assignment ----
missing_var <- ukb_subset %>%
  summarise(across(everything(), ~ mean(is.na(.)) * 100)) %>%
  pivot_longer(everything(), names_to = "variable", values_to = "pct_missing") %>%
  mutate(
    domain = case_when(
      
      # --- Explicit overrides FIRST (your requested Baseline/Psychosocial moves) ---
      str_starts(variable, "fev_avg") ~ "Psychosocial",
      
      # Baseline (match prefixes, catches .0.0 etc)
      str_starts(variable, "date_death") ~ "Baseline",
      str_starts(variable, "dx_diabetes") ~ "Baseline",
      str_starts(variable, "assessment_centre_location") ~ "Baseline",
      str_starts(variable, "bmi") ~ "Baseline",
      str_starts(variable, "date_lost_to_fup") ~ "Baseline",
      str_starts(variable, "date_recr") ~ "Baseline",
      str_starts(variable, "dob") ~ "Baseline",
      str_starts(variable, "hip_circ") ~ "Baseline",
      str_starts(variable, "sex") ~ "Baseline",
      str_starts(variable, "waist_circ") ~ "Baseline",
      str_starts(variable, "age_recr") ~ "Baseline",
      
      # keep these as Baseline too
      str_starts(variable, "menopause") ~ "Baseline",
      str_starts(variable, "cvd") ~ "Baseline",
      
      
      # --- Lifestyle ---
      str_starts(variable, "sleep") ~ "Lifestyle",
      str_starts(variable, "alc")   ~ "Lifestyle",
      str_starts(variable, "diet")  ~ "Lifestyle",
      str_starts(variable, "smoke") ~ "Lifestyle",
      str_starts(variable, "phys")  ~ "Lifestyle",
      str_starts(variable, "sed")   ~ "Lifestyle",
      
      # --- Socioeconomic ---
      str_starts(variable, "ses") ~ "Socioeconomic",
      str_starts(variable, "qualification") ~ "Socioeconomic",
      str_starts(variable, "ethnicity") ~ "Socioeconomic",
      
      # --- Psychosocial ---
      str_starts(variable, "mh") ~ "Psychosocial",
      
      # --- Environmental ---
      str_starts(variable, "env") ~ "Environmental",
      str_starts(variable, "domestic_garden") ~ "Environmental",
      str_starts(variable, "employment") ~ "Environmental",
      
      # --- Physiological ---
      str_starts(variable, "sbp") ~ "Physiological",
      str_starts(variable, "dbp") ~ "Physiological",
      variable %in% c("yob","mob","fvc","fev1","age_recr","had_menopause") ~ "Physiological",
      str_starts(variable, "preg") ~ "Physiological",
      str_starts(variable, "fvc") ~ "Psychosocial",
      
      # --- Biological ---
      str_starts(variable, "blood") ~ "Biological",
      str_starts(variable, "biochem") ~ "Biological",
      
      # --- Medical history ---
      str_starts(variable, "med") ~ "Medical history",
      
      TRUE ~ "Other"
    )
  )

# ---- Optional check: what ended up in "Other" ----
other_vars <- missing_var %>%
  filter(domain == "Other") %>%
  arrange(desc(pct_missing)) %>%
  select(variable, pct_missing)

cat("\n---- Variables in 'Other' ----\n")
print(other_vars, n = Inf)

# ---- 3) Summarise missingness per domain ----
missing_domain <- missing_var %>%
  group_by(domain) %>%
  summarise(
    n_vars = n(),
    mean_missing = mean(pct_missing),
    median_missing = median(pct_missing),
    max_missing = max(pct_missing),
    .groups = "drop"
  ) %>%
  arrange(mean_missing)

print(missing_domain)

# ---- 4) base R barplot ----
op <- par(mar = c(5, 10, 4, 2))
barplot(
  missing_domain$mean_missing,
  names.arg = missing_domain$domain,
  horiz = TRUE,
  las = 1,
  xlab = "Mean % Missing",
  main = "Mean Missingness by Domain (ukb_v2)"
)
par(op)
