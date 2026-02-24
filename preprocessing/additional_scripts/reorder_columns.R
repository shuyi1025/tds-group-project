rm(list = ls())

# load libraries
library(dplyr)
library(stringr)

# load data
ukb_v2 <- readRDS(
  "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds"
)

# fixed leading columns
front_cols <- c("eid", "cvd_event", "cvd_date")

# sanity check
stopifnot(all(front_cols %in% names(ukb_v2)))

# remaining columns
other_cols <- setdiff(names(ukb_v2), front_cols)

# helper: parse UKB-style column name
parse_col <- function(x) {
  m <- str_match(x, "^(.*?)(?:\\.(\\d+))?(?:\\.(\\d+))?$")
  tibble(
    col = x,
    base = m[, 2],
    instance = as.numeric(m[, 3]),
    array = as.numeric(m[, 4])
  )
}

parsed <- bind_rows(lapply(other_cols, parse_col))

# set the first one if no instance exists
parsed <- parsed %>%
  mutate(
    instance = ifelse(is.na(instance), -1, instance),
    array    = ifelse(is.na(array), -1, array)
  )

# sort
ordered_other_cols <- parsed %>%
  arrange(base, instance, array) %>%
  pull(col)

# final column order
final_cols <- c(front_cols, ordered_other_cols)

# reorder dataset
ukb_v2_sorted <- ukb_v2[, final_cols]


# final checks

stopifnot(
  identical(sort(names(ukb_v2)), sort(names(ukb_v2_sorted))),
  all(names(ukb_v2_sorted)[1:3] == front_cols)
)

# save
saveRDS(
  ukb_v2_sorted,
  "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds"
)
