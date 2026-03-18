rm(list = ls())
library(data.table)

ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")
data_d <- as.data.table(ukb_v2)

# 1) PNA -> NA (data_d only)
for (v in names(data_d)) {
  if (is.character(data_d[[v]]) || is.factor(data_d[[v]])) {
    x <- as.character(data_d[[v]])
    x[x == "Prefer not to answer"] <- NA_character_
    data_d[[v]] <- x
  }
}

# 2) Drop participants with NA in baseline vars (your 10 vars)
base_vars <- c("diet_spread_type",
               "diet_salt_added_food",
               "diet_milk_type",
               "diet_processed_meat_intake",
               "diet_pork_intake",
               "diet_oily_fish_intake",
               "diet_non_oily_fish_intake",
               "diet_lamb_mutton_intake",
               "diet_cereal_intake",
               "diet_beef_intake",
               "diet_fresh_fruit_intake",
               "diet_dried_fruit_intake",
               "diet_cooked_veg_intake",
               "diet_raw_veg_intake", "diet_water_intake")
base_use <- intersect(paste0(base_vars, ".0.0"), names(data_d))

cat("Original N:", nrow(data_d), "\n")
data_d <- data_d[complete.cases(data_d[, ..base_use])]
cat("After baseline drop:", nrow(data_d), "\n")

# 3) 
fv_to_num <- function(x) {
  x <- trimws(as.character(x))
  x[x %in% c("Less than once", "Less than one")] <- "0"
  x[x %in% c("-999909999", "-999909999.0")] <- NA_character_
  suppressWarnings(as.numeric(x))
}

freq_to_week <- function(x) {
  x <- as.character(x)
  out <- rep(NA_real_, length(x))
  out[x == "Never"] <- 0
  out[x == "Less than once a week"] <- 0.5
  out[x == "Once a week"] <- 1
  out[x == "2-4 times a week"] <- 3
  out[x == "5-6 times a week"] <- 5.5
  out[x == "Once or more daily"] <- 7
  out
}

# 4) Clean fruit/veg FIRST, then drop any NA in those cleaned values
data_d[, fv_fresh  := fv_to_num(diet_fresh_fruit_intake.0.0)]
data_d[, fv_dried  := fv_to_num(diet_dried_fruit_intake.0.0)]
data_d[, fv_cooked := fv_to_num(diet_cooked_veg_intake.0.0)]
data_d[, fv_raw    := fv_to_num(diet_raw_veg_intake.0.0)]

data_d <- data_d[complete.cases(fv_fresh, fv_dried, fv_cooked, fv_raw)]

# 5) Totals (now fruit/veg totals cannot be NA)
data_d[, diet_total_fish_intake :=
         freq_to_week(diet_oily_fish_intake.0.0) +
         freq_to_week(diet_non_oily_fish_intake.0.0)]

data_d[, diet_total_red_meat_intake :=
         freq_to_week(diet_lamb_mutton_intake.0.0) +
         freq_to_week(diet_beef_intake.0.0) +
         freq_to_week(diet_pork_intake.0.0)]

data_d[, diet_total_fruit_veg_intake := fv_fresh + fv_dried + fv_cooked + fv_raw]

# checks
summary(data_d$diet_total_fruit_veg_intake)
colSums(is.na(data_d[, .(diet_total_fish_intake, diet_total_red_meat_intake, diet_total_fruit_veg_intake)]))

#dichotamise data
# ---- 6) Dichotomise dietary variables (0 = meets, 1 = risk) ----

## Fruit & vegetables (servings/day)
data_d[, risk_fruit_veg :=
         fifelse(diet_total_fruit_veg_intake >= 5, 0, 1)
]

## Total fish (times/week)
data_d[, risk_fish :=
         fifelse(diet_total_fish_intake >= 2, 0, 1)
]

## Processed meat (times/week)
data_d[, risk_processed_meat :=
         fifelse(freq_to_week(diet_processed_meat_intake.0.0) <= 1, 0, 1)
]

## Total red meat (times/week)
data_d[, risk_red_meat :=
         fifelse(diet_total_red_meat_intake <= 1, 0, 1)
]

## Milk type
data_d[, risk_milk :=
         fifelse(diet_milk_type.0.0 %in% c("Semi-skimmed", "Skimmed"), 0, 1)
]

## Spread type
data_d[, risk_spread :=
         fifelse(diet_spread_type.0.0 == "Never/rarely", 0, 1)
]

## Salt added to food
data_d[, risk_salt :=
         fifelse(diet_salt_added_food.0.0 == "Never/rarely", 0, 1)
]

## Cereal intake (bowls/week)
data_d[, risk_cereal :=
         fifelse(as.numeric(diet_cereal_intake.0.0) > 5, 0, 1)
]

## Water intake (glasses/day)
data_d[, risk_water :=
         fifelse(as.numeric(diet_water_intake.0.0) >= 6, 0, 1)
]

#sum
data_d[, diet_risk_score :=
         risk_fruit_veg +
         risk_fish +
         risk_processed_meat +
         risk_red_meat +
         risk_milk +
         risk_spread +
         risk_salt +
         risk_cereal +
         risk_water
]

# quick check
summary(data_d$diet_risk_score)
table(data_d$diet_risk_score)
sum(!is.na(data_d$diet_risk_score))

#drop variables used to make score
vars_to_drop <- paste0(c(
  "diet_spread_type",
  "diet_salt_added_food",
  "diet_milk_type",
  "diet_processed_meat_intake",
  "diet_pork_intake",
  "diet_oily_fish_intake",
  "diet_non_oily_fish_intake",
  "diet_lamb_mutton_intake",
  "diet_cereal_intake",
  "diet_beef_intake",
  "diet_fresh_fruit_intake",
  "diet_dried_fruit_intake",
  "diet_cooked_veg_intake",
  "diet_raw_veg_intake",
  "diet_water_intake"
), ".0.0")

vars_to_drop <- intersect(vars_to_drop, names(data_d))
data_d[, (vars_to_drop) := NULL]