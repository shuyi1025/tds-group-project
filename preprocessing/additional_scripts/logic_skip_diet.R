rm(list = ls())

# datasetd
setwd("/rds/general/project/hda_25-26/live/TDS/TDS_Group8")
ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")
#removing alc_six_more_frequency.0.0 column, add to preprocessing_overall?
ukb_v2 <- ukb_v2[ , !names(ukb_v2) %in% c("alc_six_more_frequency.0.0")]

#practise
ukb_v22 <- ukb_v2

##coffee-------------------
#add "None" as answer to "diet_coffee_type.0.0" if "diet_coffee_intake" = 0
ukb_v22$diet_coffee_type.0.0 <- as.character(ukb_v22$diet_coffee_type.0.0)
ukb_v22$diet_coffee_type.0.0[ukb_v22$diet_coffee_intake.0.0 == 0] <- "None"
#check for changes
table(ukb_v22$diet_coffee_type.0.0, useNA = "always")


##bread----------------------------
#add "None" as answer to "diet_bread_type.0.0" if "diet_bread_intake" = 0
ukb_v22$diet_bread_type.0.0 <- as.character(ukb_v22$diet_bread_type.0.0)
ukb_v22$diet_bread_type.0.0[ukb_v22$diet_bread_intake.0.0 == 0] <- "None"
table(ukb_v22$diet_bread_type.0.0, useNA = "always")

#cereal----------------------------
ukb_v22$diet_cereal_type.0.0 <- as.character(ukb_v22$diet_cereal_type.0.0)
ukb_v22$diet_cereal_type.0.0[ukb_v22$diet_cereal_intake.0.0 == 0] <- "None"
table(ukb_v22$diet_bread_type.0.0, useNA = "always")

#weekly alcohol consumption ------------------------
ukb_v22$alc_freq.0.0 <- as.character(ukb_v22$alc_freq.0.0)
table(ukb_v22$alc_freq.0.0, useNA = "always")

# add "Special occasions only" and "Never" from alc_freq to "No" in alc_with_meals
ukb_v22$alc_with_meals.0.0 <- as.character(ukb_v22$alc_with_meals.0.0)
ukb_v22$alc_with_meals.0.0[ukb_v22$alc_freq.0.0 %in% c("Never", "Special occasions only")] <- "No"

# add "Special occasions only" and "Never" from alc_freq to "0"for alc_weekly_spirits
ukb_v22$alc_weekly_spirits.0.0 <- as.character(ukb_v22$alc_weekly_spirits.0.0)
ukb_v22$alc_weekly_spirits.0.0[ukb_v22$alc_freq.0.0 %in% c("Never", "Special occasions only")] <- "0"

# add "Special occasions only" and "Never" from alc_freq to alc_weekly_red_wine
ukb_v22$alc_weekly_red_wine.0.0[ukb_v22$alc_freq.0.0 %in% c("Never", "Special occasions only")] <- "0"
table(ukb_v22$alc_weekly_red_wine.0.0, useNA = "always")

# add "Special occasions only" and "Never" from alc_freq to alc_weekly_other_alc_drinks
ukb_v22$alc_weekly_other_alc_drinks.0.0 <- as.character(ukb_v22$alc_weekly_other_alc_drinks.0.0)
ukb_v22$alc_weekly_other_alc_drinks.0.0[ukb_v22$alc_freq.0.0 %in% c("Never", "Special occasions only")] <- "0"

# add "Special occasions only" and "Never" from alc_freq  to alc_weekly_fortified_wine
ukb_v22$alc_weekly_fortified_wine.0.0 <- as.character(ukb_v22$alc_weekly_fortified_wine.0.0)
ukb_v22$alc_weekly_fortified_wine.0.0[ukb_v22$alc_freq.0.0 %in% c("Never", "Special occasions only")] <- "0"

#add "Special occasions only" and "Never" from alc_freq  to alc_weekly_champagne_white_wine
ukb_v22$alc_weekly_champagne_white_wine.0.0 <- as.character(ukb_v22$alc_weekly_champagne_white_wine.0.0)
ukb_v22$alc_weekly_champagne_white_wine.0.0[ukb_v22$alc_freq.0.0 %in% c("Never", "Special occasions only")] <- "0"

#add "Special occasions only" and "Never" from alc_freq  to alc_weekly_beer_cider
ukb_v22$alc_weekly_beer_cider.0.0 <- as.character(ukb_v22$alc_weekly_beer_cider.0.0)
ukb_v22$alc_weekly_beer_cider.0.0[ukb_v22$alc_freq.0.0 %in% c("Never", "Special occasions only")] <- "0"

table(ukb_v22$alc_status.0.0, useNA = "always")



ukb_v2[
  , .N,
  by = .(
    CVD_timing = fifelse(
      is.na(date), "No CVD",
      fifelse(date < date_recr.0.0, "Before baseline", "After baseline")
    )
  )
][
  , Proportion := N / sum(N)
]

