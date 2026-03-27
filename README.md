# TDS Group 8 – Exposome & CVD Risk Pipeline

This repository contains the data processing and modelling pipeline for analysing external exposome factors associated with 10-year incident cardiovascular disease (CVD) using UK Biobank data.

#### This project is designed to run on the Imperial College HPC.

------------------------------------------------------------------------

## 📁 Project Structure

```         
TDS_Group8/
├── extraction_and_recoding/    # extraction + recoding workflow
├── pipeline_scripts/           # main preprocessing / imputation / downstream / Aims scripts
    ├── preprocessing
    ├── imputation
    ├── post_imputation
    ├── Aim 1
    ├── Aim 2&3
    ├── Aim 4
├── pipeline_outputs/           # generated outputs
```

## 🚀 How to Run

### 0. Before beginning, please cd to the working directory.

### 1. Extraction & Recoding (HPC jobs)

Submit the extraction and recoding job scripts:

``` bash
qsub extraction_and_recoding/1-generate_data_dict.sh
qsub extraction_and_recoding/2-extract_selected.sh
qsub extraction_and_recoding/3-recode_extracted.sh
```

### 2. Preprocessing

#### Option A: Render the full R Markdown report

This will run the full workflow and generate the report output.

``` bash
Rscript -e "rmarkdown::render('pipeline_scripts/final_preprocessing.Rmd', output_format = 'html_document')"
```

#### Option B: Open the file for inspection and run code chunks (Recommended)

``` bash
nano pipeline_scripts/final_preprocessing.Rmd
```

### 3. Imputation (HPC job)

Submit the imputation job script:

``` bash
qsub pipeline_scripts/imputation.sh
```

### 4. Downstream

``` bash
Rscript -e "rmarkdown::render('pipeline_scripts/post_imputation_script.Rmd', output_format = 'html_document')"
```

#### Option B: Open the file for inspection and run code chunks (Recommended)

``` bash
nano pipeline_scripts/post_imputation_script.Rmd
```

### 5. Aim 1

``` bash
nano pipeline_scripts/Aim1.Rmd
```

### 6. Aim 2&3

``` bash
nano pipeline_scripts/Aim2_3.Rmd
```
### 7.📁 Aim 4
This folder contains four machine learning models used in Aim 4:

logistic.ipynb — Logistic Regression
``` bash
nano pipeline_scripts/Aim4/logistic.ipynb
```
random_forest.ipynb — Random Forest
``` bash
nano pipeline_scripts/Aim4/random_forest.ipynb
```
XGboost.ipynb — XGBoost
``` bash
nano pipeline_scripts/Aim4/XGboost.ipynb
```
NN.ipynb — Neural Network
``` bash
nano pipeline_scripts/Aim4/NN.ipynb
```

Each notebook is designed to run on three alternative training datasets.
To switch between datasets, modify the data path at the beginning of the notebook.

Available Datasets

The following datasets can be used for Aim 4:
1. Baseline variables only: "../pipeline_outputs/aim1_output/ukb_train_baseline.csv"
2. Baseline + external exposome one-hot encoded variables: "../pipeline_outputs/aim1_output/train_baseline_ee_onehot.csv"
3. Baseline + selected external exposome/biomarker features after stability selection and clustering: "../pipeline_outputs/aim2_3_output/train_ee_bio_stable_allclusters.csv"

## Dependencies

```         
- dplyr
- lubridate
- stringr
- data.table
- openxlsx
- miceRanger
- caret
- doParallel
- glmnet
- sharp
- ggplot2
- GGally
- corrplot
- uwot
- pROC
```
