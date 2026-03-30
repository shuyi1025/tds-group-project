# load libraries 

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
import os

# 1) Baseline AUC ROC combined

# Define output directory
output_dir = "../../pipeline_outputs/aim4_output/auc_overlay"

models = {
    "Logistic Regression": "logistic_baseline.csv",
    "Random Forest": "rf_baseline.csv",
    "XGBoost": "xgb_baseline.csv",
    "Neural Network": "nn_baseline.csv"
}

plt.figure(figsize=(8,6))

for name, file in models.items():
    path = os.path.join(output_dir, file)
    df = pd.read_csv(path)
    
    y_true = df["y_true"]
    y_pred = df["y_pred"]
    
    fpr, tpr, _ = roc_curve(y_true, y_pred)
    roc_auc = auc(fpr, tpr)
    
    plt.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc:.3f})")

# diagonal line
plt.plot([0,1], [0,1], linestyle="--")

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Baseline ROC Curves Comparison")
plt.legend()
plt.grid()

plt.savefig(os.path.join(output_dir, "baseline_combined_roc.png"), dpi=300)
plt.show()

# 2) Baseline + external exposome AUC ROC 

# Define output directory
output_dir = "../output"

models = {
    "Logistic Regression": "logistic_baseline_ee.csv",
    "Random Forest": "rf_baseline_ee.csv",
    "XGBoost": "xgb_baseline_ee.csv",
    "Neural Network": "nn_baseline_ee.csv"
}

plt.figure(figsize=(8,6))

for name, file in models.items():
    path = os.path.join(output_dir, file)
    df = pd.read_csv(path)
    
    y_true = df["y_true"]
    y_pred = df["y_pred"]
    
    fpr, tpr, _ = roc_curve(y_true, y_pred)
    roc_auc = auc(fpr, tpr)
    
    plt.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc:.3f})")

# diagonal line
plt.plot([0,1], [0,1], linestyle="--")

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Baseline + External Exposome ROC Curves Comparison")
plt.legend()
plt.grid()

plt.savefig(os.path.join(output_dir, "baseline_ee_combined_roc.png"), dpi=300)
plt.show()

# 3) Baseline + EE + biomarker AUC ROC

# Define output directory
output_dir = "../output"

models = {
    "Logistic Regression": "logistic_baseline_ee_biomarker.csv",
    "Random Forest": "rf_baseline_ee_biomarker.csv",
    "XGBoost": "xgb_baseline_ee_biomarker.csv",
    "Neural Network": "nn_baseline_ee_biomarker.csv"
}

plt.figure(figsize=(8,6))

for name, file in models.items():
    path = os.path.join(output_dir, file)
    df = pd.read_csv(path)
    
    y_true = df["y_true"]
    y_pred = df["y_pred"]
    
    fpr, tpr, _ = roc_curve(y_true, y_pred)
    roc_auc = auc(fpr, tpr)
    
    plt.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc:.3f})")

# diagonal line
plt.plot([0,1], [0,1], linestyle="--")

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("Baseline + External Exposome + Biomarker ROC Curves Comparison")
plt.legend()
plt.grid()

plt.savefig(os.path.join(output_dir, "baseline_ee_biomarker_combined_roc.png"), dpi=300)
plt.show()
