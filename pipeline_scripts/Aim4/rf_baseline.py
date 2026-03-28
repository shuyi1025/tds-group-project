import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import (
    roc_auc_score, roc_curve, accuracy_score, confusion_matrix,
    precision_score, recall_score, f1_score, classification_report
)

from sklearn.ensemble import RandomForestClassifier

outcome = "cvd_event"
eid = "eid"

print("Loading datasets...")

train = pd.read_csv("../pipeline_outputs/ukb_train_baseline.csv")  #change file names accordingly
test = pd.read_csv("../pipeline_outputs/ukb_test_baseline.csv")

# Split predictors and outcome
X_train = train.drop(columns=[outcome, eid])
y_train = train[outcome]

X_test = test.drop(columns=[outcome, eid])
y_test = test[outcome]

print("Train shape:", X_train.shape)
print("Test shape:", X_test.shape)


# identify column types

numeric_cols = X_train.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X_train.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

print("Numeric columns:", len(numeric_cols))
print("Categorical columns:", len(cat_cols))


# Preprocessing
print("Preprocessing data...")

preprocessor = ColumnTransformer(
    transformers=[
        ("num", "passthrough", numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
    ]
)

X_train_proc = preprocessor.fit_transform(X_train)
X_test_proc = preprocessor.transform(X_test)

print("Processed train shape:", X_train_proc.shape)
print("Processed test shape:", X_test_proc.shape)


# Handle class imbalance
n_pos = y_train.sum()
n_neg = len(y_train) - n_pos

print("Positive cases:", int(n_pos))
print("Negative cases:", int(n_neg))


print("Training Random Forest model...")

rf_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=6,
    min_samples_split=20,
    min_samples_leaf=10,
    max_features="sqrt",
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train_proc, y_train)

print("Model training complete.")


print("Evaluating Random Forest model...")

# Collect probabilities batch-wise 
probs = rf_model.predict_proba(X_test_proc)[:, 1]
preds = (probs > 0.5).astype(int)

# Compute metrics
test_auc = roc_auc_score(y_test, probs)
test_acc = accuracy_score(y_test, preds)
test_precision = precision_score(y_test, preds)
test_recall = recall_score(y_test, preds)
test_f1 = f1_score(y_test, preds)

# Save metrics to CSV
metrics_df = pd.DataFrame({
    "AUC": [test_auc],
    "Accuracy": [test_acc],
    "Precision": [test_precision],
    "Recall": [test_recall],
    "F1": [test_f1]
})
metrics_df.to_csv("rf_model_metrics_baseline.csv", index=False)

# Confusion matrix and classification report
cm = confusion_matrix(y_test, preds)
report = classification_report(y_test, preds)

# Print results
print("\n===== Test Results =====")
print("AUC:", round(test_auc, 4))
print("Accuracy:", round(test_acc, 4))
print("Precision:", round(test_precision, 4))
print("Recall:", round(test_recall, 4))
print("F1 Score:", round(test_f1, 4))
print("\nConfusion Matrix:\n", cm)
print("\nClassification Report:\n", report)


results_df = pd.DataFrame({
    "AUC":[test_auc],
    "Accuracy":[test_acc]
})

results_df.to_csv("rf_results_baseline.csv", index=False)

print("Saved results.")


print("Saving ROC curve...")

fpr, tpr, thresholds = roc_curve(y_test, probs)

plt.figure(figsize=(6,5))
plt.plot(fpr, tpr, label=f"Random Forest (AUC={test_auc:.3f})")
plt.plot([0,1],[0,1],"--")

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve - Random Forest")
plt.legend()

plt.tight_layout()
plt.savefig("rf_roc_curve_baseline.png", dpi=300)
plt.close()


print("Calculating feature importance...")

feature_names = preprocessor.get_feature_names_out()
importances = rf_model.feature_importances_

importance_df = pd.DataFrame({
    "feature": feature_names,
    "importance": importances
}).sort_values("importance", ascending=False)

print("\nTop 20 Features:")
print(importance_df.head(20))

importance_df.to_csv("rf_feature_importance_baseline.csv", index=False)

# Plot top features
top_k = 20
top_importance = importance_df.head(top_k).iloc[::-1]

plt.figure(figsize=(8,6))
plt.barh(top_importance["feature"], top_importance["importance"])

plt.xlabel("Importance")
plt.title(f"Top {top_k} Random Forest Feature Importances")

plt.tight_layout()
plt.savefig("rf_feature_importance_baseline.png", dpi=300)
plt.close()

