# TDS Group 8 – Exposome & CVD Risk Pipeline

This repository contains the data processing and modelling pipeline for analysing external exposome factors associated with 10-year incident cardiovascular disease (CVD) using UK Biobank data.

#### This project is designed to run on the Imperial College HPC.

------------------------------------------------------------------------

## 📁 Project Structure

```         
TDS_Group8/
├── extraction_and_recoding/    # extraction + recoding workflow
├── pipeline_scripts/           # main preprocessing / imputation / downstream / Aim 1 scripts
    ├── preprocessing
    ├── imputation
    ├── post_imputation
    ├── Aim 1
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
Rscript -e "rmarkdown::render('pipeline_scripts/preprocessing/final_preprocessing.Rmd', output_format = 'html_document')"
```

#### Option B: Open the file for inspection and run code chunks (Recommended)

``` bash
nano pipeline_scripts/preprocessing/final_preprocessing.Rmd
```

### 3. Imputation (HPC job)

Submit the imputation job script:

``` bash
qsub pipeline_scripts/imputation.sh
```

### 4. Downstream

``` bash
Rscript -e "rmarkdown::render('pipeline_scripts/preprocessing/post_imputation_script.Rmd', output_format = 'html_document')"
```

#### Option B: Open the file for inspection and run code chunks (Recommended)

``` bash
nano pipeline_scripts/preprocessing/post_imputation_script.Rmd
```

### 5. Aim 1

``` bash
nano pipeline_scripts/preprocessing/Aim1.Rmd
```

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
```
