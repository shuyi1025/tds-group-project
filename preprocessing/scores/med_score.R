# med_score

# currently have the code to ignore NAs and PNAs and only account for meds and "None of the above"

library(dplyr)
library(stringr)

med_cols <- grep("^med_chol_bp_diabetes\\.0\\.[0-3]+$",
                 names(ukb_v2),
                 value = TRUE)

ukb_v2 <- ukb_v2 %>%
  rowwise() %>%
  mutate(
    med_score_chol_bp_diabetes = {meds <- c_across(all_of(med_cols)) %>%
        as.character() %>%
        str_trim()
      
      # If any col in row has "None of the above" → 0
      
      if ("None of the above" %in% meds) {0} 
      else {meds_clean <- meds[!is.na(meds) & meds != "Prefer not to answer"]
      length(unique(meds_clean))
      }
    }
  ) %>%
  ungroup()

# table to check the above works properly

med <- ukb_v2%>%
  select(eid,med_chol_bp_diabetes.0.0, med_chol_bp_diabetes.0.1, med_chol_bp_diabetes.0.2, med_score_chol_bp_diabetes)

# histogram for distribution check 

library(ggplot2)

ggplot(ukb_v2, aes(x = med_score_chol_bp_diabetes)) +
  geom_histogram(
    binwidth = 1,
    boundary = -0.5,
    closed = "right"
  ) +
  scale_x_continuous(breaks = 0:3) +
  labs(
    title = "Distribution of Medication Score",
    x = "Medication Score",
    y = "Count"
  ) +
  theme_minimal()


