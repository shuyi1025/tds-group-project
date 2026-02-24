library(miceRanger)
ukb_v3_10 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/imputation/ukb_v3_10.rds")

# variables used for imputation
pred_list <- c(
  "ses_commute_distance_home_to_work.0.0",
  "smoke_tobacco_exposure_outside.0.0",
  "ses_length_working_week.0.0",
  "ses_accom_own_or_rent.0.0",
  "smoke_age_start_current.0.0",
  "smoke_cig_daily_previous.0.0",
  "smoke_tobacco_exposure_home.0.0",
  "smoke_age_stop.0.0",
  "mh_freq_visit.0.0",
  "diet_bread_intake.0.0",
  "ses_commute_frequency.0.0",
  "ses_age_completed_full_time_education.0.0",
  "dx_diabetes.0.0",
  "smoke_age_start_former_smoker.0.0",
  "smoke_number_cig_previous_current_cigar_pipe.0.0",
  "diet_raw_veg_intake.0.0",
  "mh_frequency_tiredness_2_weeks.0.0",
  "diet_cooked_veg_intake.0.0",
  "smoke_age_stopped_cig.0.0",
  "diet_cheese_intake.0.0",
  "diet_dried_fruit_intake.0.0",
  "ses_household_size.0.0",
  "ethnicity.0.0",
  "mh_confide.0.0",
  "diet_coffee_intake.0.0",
  "smoke_number_daily_current_smoker.0.0",
  "sleep_insomnia.0.0",
  "ses_job_mainly_walking_or_standing.0.0",
  "diet_tea_intake.0.0",
  "sleep_duration.0.0",
  "diet_water_intake.0.0",
  "diet_fresh_fruit_intake.0.0",
  "med_pain_relief_constipation_heartburn.0.5",
  "diet_poultry_intake.0.0",
  "diet_oily_fish_intake.0.0",
  "diet_cereal_intake.0.0",
  "sed_computer_use_time.0.0",
  "sed_drive.0.0",
  "med_chol_bp_diabetes_hormones.0.2",
  "diet_beef_intake.0.0",
  "diet_lamb_mutton_intake.0.0",
  "diet_non_oily_fish_intake.0.0",
  "med_pain_relief_constipation_heartburn.0.1",
  "sed_weekly_phone_usage_3m.0.0",
  "med_chol_bp_diabetes.0.0",
  "ses_job_heavy_manual_or_physical_work.0.0",
  "smoke_maternal_around_birth.0.0",
  "med_chol_bp_diabetes_hormones.0.0",
  "ses_household_income_before_tax_avg.0.0",
  "diet_variation.0.0",
  "sed_tv_watching_time.0.0",
  "sed_mobile_phone_use_length.0.0",
  "med_chol_bp_diabetes_hormones.0.1",
  "diet_pork_intake.0.0",
  "mh_frequency_tenseness_2_weeks.0.0",
  "diet_processed_meat_intake.0.0",
  "med_pain_relief_constipation_heartburn.0.4",
  "ses_job_shift_work.0.0",
  "diet_milk_type.0.0",
  "mh_frequency_unenthusiasm_2_weeks.0.0",
  "mh_frequency_depression_2_weeks.0.0",
  "sleep_daytime_nap.0.0",
  "sleep_daytime_dozing.0.0",
  "med_pain_relief_constipation_heartburn.0.0",
  "alc_with_meals.0.0",
  "med_chol_bp_diabetes_hormones.0.3",
  "diet_spread_type.0.0",
  "diet_bread_type.0.0",
  "diet_cereal_type.0.0",
  "med_chol_bp_diabetes.0.2",
  "med_other.0.0",
  "mh_risk_taking.0.0",
  "sleep_chronotype.0.0",
  "med_pain_relief_constipation_heartburn.0.2",
  "med_chol_bp_diabetes.0.1",
  "diet_coffee_type.0.0",
  "med_pain_relief_constipation_heartburn.0.3",
  "sleep_snore.0.0",
  "sleep_falling_asleep_trouble.0.0",
  "sleep_too_much.0.0",
  "sleep_wake_early.0.0",
  "sleep_change.0.0"
)

n_cores <- as.integer(Sys.getenv("PBS_NCPUS", "1"))
ukb_imp_data <- ukb_v3_10[, !names(ukb_v3_10) %in% "cvd_event"]

# impute data
impute <- miceRanger::miceRanger(
  ukb_imp_data,
  m = 1,                # one imputed dataset
  maxiter = 3,          # number of iterations
  num.trees = 50,       # random forest size
  verbose = TRUE,
  vars = pred_list,
  num.threads = n_cores
)

# extract imputed data
ukb_v4_10 <- as.data.frame(completeData(impute)[[1]])
saveRDS(ukb_v4_10, "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/imputation/ukb_v4_10.rds")