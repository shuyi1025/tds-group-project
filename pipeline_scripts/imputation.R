start_time <- Sys.time()
message("===== Imputation job started at: ", start_time, " =====")

# Load libraries
library(miceRanger)
library(dplyr)
library(caret)
library(doParallel)

# Load data
ukb <- readRDS("../pipeline_outputs/pre_output/ukb_raw.rds")

# Ensure characters are factors
ukb[] <- lapply(ukb, function(x) if (is.character(x)) as.factor(x) else x)

# Split train/test (70/30)
set.seed(123)
train_idx <- caret::createDataPartition(ukb$cvd_event, p = 0.7, list = FALSE)
train_data <- ukb[train_idx, ]
test_data  <- ukb[-train_idx, ]
message("Train rows: ", nrow(train_data), " | Test rows: ", nrow(test_data))

# Identify variables to impute
missing_rate <- sapply(ukb, function(x) mean(is.na(x)))
pred_list <- names(missing_rate[missing_rate > 0])
exclude_vars <- c("cvd_date")
pred_list <- setdiff(pred_list, exclude_vars)

pred_train <- intersect(pred_list, names(train_data))
pred_test  <- intersect(pred_list, names(test_data))

# Align factor levels in test to match train
for (v in pred_test) {
  if (is.factor(train_data[[v]])) {
    test_data[[v]] <- factor(test_data[[v]], levels = levels(train_data[[v]]))
  }
}

# Setup parallel backend
num_threads <- as.numeric(Sys.getenv("PBS_NP"))
if (is.na(num_threads) || num_threads == 0) num_threads <- parallel::detectCores()/4
cl <- makeCluster(num_threads)
registerDoParallel(cl)
message("Using ", getDoParWorkers(), " threads for parallel imputation")

# train imputation 

imp_start <- Sys.time()
message("Train imputation started at: ", imp_start)

set.seed(123)
impute_train <- miceRanger(
  data        = train_data[, pred_train],
  m           = 1,
  maxiter     = 10,
  num.trees   = 100,
  verbose     = TRUE,
  parallel    = TRUE,
  num.threads = num_threads,
  saveModels  = TRUE,      # save RF for test imputation
  returnModels = TRUE,     # must return RF to be reused
  returnRF    = TRUE
)

imp_end <- Sys.time()
message("Train imputation finished at: ", imp_end)
message("Elapsed time: ", imp_end - imp_start)

# Complete train data
train_complete <- completeData(impute_train)[[1]]
train_data[, pred_train] <- train_complete

# test imputation (uses train tf as test rf)
imp_test_start <- Sys.time()
message("Test imputation started at: ", imp_test_start)

set.seed(123)
impute_test <- miceRanger(
  data        = test_data[, pred_test],
  m           = 1,
  maxiter     = 10,
  num.trees   = 100,       # same as train
  verbose     = TRUE,
  parallel    = TRUE,
  num.threads = num_threads,
  saveModels  = FALSE,      # no need to save again
  returnModels = FALSE,     
  returnRF    = FALSE,
  forest      = impute_train$rfImpute  # <-- reuse train RF
)

# Complete test data
test_complete <- completeData(impute_test)[[1]]
test_data[, pred_test] <- test_complete

imp_test_end <- Sys.time()
message("Test imputation finished at: ", imp_test_end)
message("Elapsed test train time: ", imp_test_end - imp_test_start)

# stop cluster
stopCluster(cl)
registerDoSEQ()

# Report remaining NAs
message("Remaining NA in train: ", sum(is.na(train_data[, pred_train])))
message("Remaining NA in test: ", sum(is.na(test_data[, pred_test])))

# Save completed train & test data
output_dir <- "../pipeline_outputs/imputation_output"
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

saveRDS(train_data, file.path(output_dir, "ukb_train.rds"))
saveRDS(test_data, file.path(output_dir, "ukb_test.rds"))

# Script end
end_time <- Sys.time()
message("===== Script finished at: ", end_time, " =====")
message("Total runtime: ", end_time - start_time)