rm(list = ls())

library(dplyr)

ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")

#drop columns
ukb_drop <- ukb_v2 %>% select(-alc_six_more_frequency.0.0, -alc_drinker_former.0.0, -alc_amount_daily.0.0,-alc_weekly_spirits.0.0,-alc_weekly_red_wine.0.0,-alc_weekly_other_alc_drinks.0.0,-alc_weekly_fortified_wine.0.0,-alc_weekly_champagne_white_wine.0.0,-alc_weekly_beer_cider.0.0,-alc_monthly_spirits.0.0,-alc_monthly_red_wine.0.0,-alc_monthly_other_alcohol_drink.0.0,-alc_monthly_champagne_white_wine.0.0,-alc_monthly_beer_cider.0.0)

#check
c("alc_six_more_frequency.0.0",
  "alc_drinker_former.0.0",
  "alc_amount_daily.0.0","alc_weekly_spirits.0.0",
"alc_weekly_red_wine.0.0",
"alc_weekly_other_alc_drinks.0.0",
"alc_weekly_fortified_wine.0.0",
"alc_weekly_champagne_white_wine.0.0",
"alc_weekly_beer_cider.0.0",
"alc_monthly_spirits.0.0",
"alc_monthly_red_wine.0.0",
"alc_monthly_other_alcohol_drink.0.0",
"alc_mothly_fortified_wine.0.0",
"alc_monthly_champagne_white_wine.0.0",
"alc_monthly_beer_cider.0.0") %in% names(ukb_drop)

# save cleaned dataset
saveRDS(ukb_drop,"/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")
