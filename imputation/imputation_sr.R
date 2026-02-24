#work in progress not final -> does not run

set.seed(1)

# ---- Libraries ----
library(rsample)
library(dplyr)
library(missForest)
library(foreach)
library(doParallel)

# ---- Register Parallel Backend ----
ncores <- as.integer(Sys.getenv("PBS_NCPUS"))
if (is.na(ncores) || ncores < 1) ncores <- 1

cl <- makeCluster(ncores)
registerDoParallel(cl)

cat("Using", ncores, "cores\n")

# ---- 1) Load ----
ukb_v2 <- readRDS("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/final_recode/ukb_v2.rds")

# ---- 2) Split 30/70 (stratified) ----
split_obj <- initial_split(ukb_v2, prop = 0.30, strata = cvd_event)
train_data <- training(split_obj)
test_data  <- testing(split_obj)

# ---- 3) Remove non-predictors / leakage ----
train_data <- train_data %>% select(-eid, -cvd_date)
test_data  <- test_data  %>% select(-eid, -cvd_date)

# ---- 4) Impute ----
cat("Starting train imputation...\n")
mf_train <- missForest(train_data, maxiter = 3, ntree = 50, parallelize = "forests")
train_imp <- mf_train$ximp

cat("Starting test imputation...\n")
mf_test <- missForest(test_data, maxiter = 3, ntree = 50, parallelize = "forests")
test_imp <- mf_test$ximp

# ---- Stop Cluster ----
stopCluster(cl)

# ---- 5) Save ----
saveRDS(train_imp, "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/imputation/train_imputed.rds")
saveRDS(test_imp,  "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/imputation/test_imputed.rds")

cat("Imputation complete.\n")

