rm(list = ls())

# merging dbp_automated & dbp_manual

ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")

# dbp_average

ukb_collapsed <- ukb_v2 %>%
  mutate(dbp_avg = rowMeans(select(., dbp_automated.0.0, dbp_automated.0.1, dbp_manual.0.0, dbp_manual.0.1),
                            na.rm = TRUE)) %>%
  select(-dbp_automated.0.0, -dbp_automated.0.1,
         -dbp_manual.0.0, -dbp_manual.0.1)

# merging sbp_automated & sbp_manual
# replace 8242 with NA in sbp_automated.0.0 & sbp_automated.0.1

ukb_collapsed <- ukb_v2%>%
  mutate(across(c(sbp_automated.0.0, sbp_automated.0.1), ~ replace(., . == 8242, NA)))


# can do this after discussing what to do with sbp NA
ukb_collapsed <- ukb_v2 %>%
  mutate(sbp_avg = rowMeans(select(., sbp_automated.0.0, sbp_automated.0.1, sbp_manual.0.0, sbp_manual.0.1),
      na.rm = TRUE)) %>%
  select(-sbp_automated.0.0, -sbp_automated.0.1,
         -sbp_manual.0.0, -sbp_manual.0.1)

# exclude individuals who had CVD before baseline

ukb_collapsed <- ukb_collapsed %>%
  mutate(baseline_cvd = ifelse(!is.na(date) & date < date_recr.0.0, 0, 1))

ukb_collapsed <- ukb_collapsed %>%
  filter(baseline_cvd == 1)%>%
  select(-baseline_cvd)

# removing all extra variables

ukb_v2 <- ukb_v2%>%
  select(-qualification.0.0, -qualification.0.1, -qualification.0.2, -qualification.0.3, -qualification.0.4,
         -qualification.0.5, -env_greenspace_pct_buffer_1000m.0.0, -age_recr.0.0, -env_natural_env_perc_1000.0.0,
         -env_no2_air_pollution_2005.0.0, -env_no2_air_pollution_2006.0.0, -env_no2_air_pollution_2007.0.0, -env_water_perc_1000.0.0,
         -yob.0.0, -mob.0.0, -dbp_automated.0.0, -dbp_automated.0.1, -dbp_manual.0.0, -dbp_manual.0.1)




