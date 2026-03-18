# TDS Group 8 – Exposome & CVD Risk Pipeline

This repository contains the data processing and modelling pipeline for analysing external exposome factors associated with 10-year incident cardiovascular disease (CVD) using UK Biobank data.

#### This project is designed to run on the Imperial College HPC.

------------------------------------------------------------------------

## 📁 Project Structure

```         
TDS_Group8/
├── extraction_and_recoding/    # extraction + recoding workflow
├── pipeline_scripts/           # main preprocessing / imputation / downstream scripts
    ├── preprocessing
    ├── imputation
    ├── post_imputation
├── pipeline_outputs/           # generated outputs
```

## 🚀 How to Run

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

### 4. Downstream

## Dependencies

```         
- dplyr (version 1.2.0)
- lubridate (version 1.9.5)
- stringr (version 1.6.0)
- data.table (version 1.18.2.1)
- openxlsx (version 4.2.8.1)
```
