rm(list = ls())

# load libraries

library(dplyr)

# load data

ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")
ukb_drop <- ukb_v2

# dropping employment_chemical_fume, employment_cigarette_smoke and taking the latest instance for employment_noise

ukb_drop <- ukb_drop %>%
  mutate(employment_noise = employment_noise.0.39)%>%
  select(-matches("^employment_noise\\.0\\."), -matches("^employment_chemical_fume\\.0\\."),
         -matches("^employment_cigarette_smoke\\.0\\."))

# taking the last instance for ses_commute_transport_type

transport_cols_latest <- grep("^ses_commute_transport_type\\.0\\.[1-4]$",
                              names(ukb_drop),
                              value = TRUE)

ukb_drop <- ukb_drop %>%
  mutate(
    ses_transport_type = ses_commute_transport_type.0.3
  ) %>%
  select(-setdiff(transport_cols, "ses_commute_transport_type.0.3"))

# take the latest qualification col

qualification_cols <- grep("^qualification\\.0\\.[1-5]$",
                              names(ukb_drop),
                              value = TRUE)

ukb_drop <- ukb_drop %>%
  mutate(
    qualification = qualification.0.5
  ) %>%
  select(-setdiff(qualification_cols, "qualification.0.5"))

# taking latest instance for ses_current_employment_status

employment_stat_cols <- grep("^ses_current_employment_status\\.0\\.[0-6]$",
                           names(ukb_drop),
                           value = TRUE)

ukb_drop <- ukb_drop %>%
  mutate(
    employment_stat = ses_current_employment_status.0.6
  ) %>%
  select(-setdiff(employment_stat_cols, "ses_current_employment_status.0.6"))

# keep only one of the death status (they are both the exact same)

ukb_v2$date_death.0.0.1

# dropping vars

ukb_drop <- ukb_drop%>%
  select(-age_recr.0.0, -env_greenspace_pct_buffer_1000m.0.0, -env_natural_env_perc_1000.0.0, -env_no2_air_pollution_2005.0.0,
         -env_no2_air_pollution_2006.0.0, -env_no2_air_pollution_2007.0.0, -env_water_perc_1000.0.0, -sbp_automated.0.0,
         -sbp_automated.0.1)

# average dbp_automated and dbp_manual cols

ukb_drop <- ukb_drop %>%
  mutate(dbp_avg = rowMeans(select(., dbp_automated.0.0, dbp_automated.0.1, dbp_manual.0.0, dbp_manual.0.1),
                            na.rm = TRUE)) %>%
  select(-dbp_automated.0.0, -dbp_automated.0.1,
         -dbp_manual.0.0, -dbp_manual.0.1)

# average sbp_manuals cols

ukb_drop <- ukb_drop%>%
  mutate(sbp_avg = rowMeans(select(., sbp_manual.0.0, sbp_manual.0.1), na.rm = TRUE))%>%
  select(-sbp_manual.0.0, -sbp_manual.0.1)

# average fev and fvc as multiple blows are done so should take an average 

ukb_drop <- ukb_drop%>%
  mutate(fev_avg = rowMeans(select(., fev1.0.0, fev1.0.1, fev1.0.2), na.rm = TRUE))%>%
  mutate(fvc_avg = rowMeans(select(., fvc.0.0, fvc.0.1, fvc.0.2), na.rm = TRUE))%>%
  select(-fvc.0.0, -fvc.0.1, -fvc.0.2,
         -fev1.0.0, -fev1.0.1, -fev1.0.2)

# leave medication cols
# what to do with mh_activities cols?


# keep the latest mh_activities col??

ukb_v2 <- ukb_v2[, !grepl("mh_activities\\.0\\.[0-3]$", names(ukb_v2))]