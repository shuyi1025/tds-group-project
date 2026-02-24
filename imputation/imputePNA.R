vars_to_imputePNA<- c(
  "diet_bread_intake.0.0",
  "diet_bread_type.0.0",
  "diet_cereal_intake.0.0",
  "diet_cereal_type.0.0",
  "diet_coffee_intake.0.0",
  "diet_coffee_type.0.0",
  "med_chol_bp_diabetes.0.0",
  "med_chol_bp_diabetes.0.1",
  "med_chol_bp_diabetes.0.2",
  "med_chol_bp_diabetes_hormones.0.0",
  "med_chol_bp_diabetes_hormones.0.1",
  "med_chol_bp_diabetes_hormones.0.2",
  "med_chol_bp_diabetes_hormones.0.3",
  "med_pain_relief_constipation_heartburn.0.0",
  "med_pain_relief_constipation_heartburn.0.1",
  "med_pain_relief_constipation_heartburn.0.2",
  "med_pain_relief_constipation_heartburn.0.3",
  "med_pain_relief_constipation_heartburn.0.4",
  "med_pain_relief_constipation_heartburn.0.5",
  "sleep_snore.0.0",
  "sleep_chronotype.0.0",
  "sleep_insomnia.0.0",
  "sleep_duration.0.0",
  "sleep_daytime_dozing.0.0"
)

ukb_v3 <- ukb_v2
ukb_v3[vars_to_imputePNA] <- lapply(
  ukb_v3[vars_to_imputePNA],
  function(x) {
    x[x == "Prefer not to answer"] <- NA
    return(x)
  }
)

saveRDS(ukb_v3, file = "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/imputation/ukb_v3.rds")