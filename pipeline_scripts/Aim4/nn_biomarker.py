import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    roc_auc_score, roc_curve, accuracy_score, confusion_matrix,
    precision_score, recall_score, f1_score, classification_report
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def sparse_to_tensor(sparse_matrix, dtype=torch.float32):
    """Convert sparse matrix to PyTorch tensor efficiently."""
    if hasattr(sparse_matrix, "toarray"):
        return torch.tensor(sparse_matrix.toarray(), dtype=dtype)
    return torch.tensor(sparse_matrix, dtype=dtype)

print("conversion function ready")

outcome = "cvd_event"
eid = "eid"

train = pd.read_csv("../pipeline_outputs/train_ee_bio_stable_allclusters.csv")  ##change file names accordingly
test = pd.read_csv("../pipeline_outputs/test_ee_bio_stable_allclusters.csv")

X_train = train.drop(columns=[outcome, eid])
y_train = train[outcome]
X_test = test.drop(columns=[outcome, eid])
y_test = test[outcome]

print("train test sets defined")


# Identify column types

numeric_cols = X_train.select_dtypes(include=["int64","float64"]).columns.tolist()
cat_cols = X_train.select_dtypes(include=["object","category","bool"]).columns.tolist()

# Preprocessing
preprocessor = ColumnTransformer([
    ("num", StandardScaler(), numeric_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
])

X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

# Convert to tensors
X_train_t = sparse_to_tensor(X_train_processed)
X_test_t = sparse_to_tensor(X_test_processed)
y_train_t = torch.tensor(y_train.values, dtype=torch.float32).view(-1,1)
y_test_t = torch.tensor(y_test.values, dtype=torch.float32).view(-1,1)

# DataLoaders
train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=64, shuffle=True)
test_loader = DataLoader(TensorDataset(X_test_t, y_test_t), batch_size=64)

print("Preprocessing complete")

class UKBN(nn.Module):
    def __init__(self, input_dim, hidden_sizes=(128,64), dropout=0.3):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_sizes:
            layers.append(nn.Linear(prev,h))
            layers.append(nn.BatchNorm1d(h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev = h
        layers.append(nn.Linear(prev,1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

print("Model setup")

num_pos = y_train_t.sum()
num_neg = y_train_t.shape[0] - num_pos
pos_weight = torch.tensor([num_neg / num_pos], dtype=torch.float32).to(device)

model = UKBN(input_dim=X_train_t.shape[1], dropout=0.3).to(device)
criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
optimizer = optim.Adam(model.parameters(), lr=0.001)
n_epochs = 50

print("complete")



# Track training loss
train_losses = []

# Training loop
for epoch in range(n_epochs):
    model.train()
    epoch_loss = 0
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        optimizer.zero_grad()
        logits = model(xb)
        loss = criterion(logits, yb)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    train_losses.append(epoch_loss)
    print(f"Epoch {epoch+1}/{n_epochs} Loss: {epoch_loss:.4f}")

print("train complete")


plt.figure()
plt.plot(train_losses)
plt.xlabel("Epoch")
plt.ylabel("Training Loss")
plt.title("Neural Network Training Loss")
plt.savefig("nn_training_loss_biomarker.png", dpi=300)
plt.close()

print("training curve saved")


model.eval()
probs = []
with torch.no_grad():
    for xb, yb in test_loader:
        xb = xb.to(device)
        logits = model(xb)
        p = torch.sigmoid(logits).cpu().numpy()
        probs.extend(p)

probs = np.array(probs).flatten()
preds = (probs > 0.5).astype(int)

# Compute metrics
auc = roc_auc_score(y_test, probs)
acc = accuracy_score(y_test, preds)
precision = precision_score(y_test, preds)
recall = recall_score(y_test, preds)
f1 = f1_score(y_test, preds)

metrics_df = pd.DataFrame({
    "AUC":[auc],
    "Accuracy":[acc],
    "Precision":[precision],
    "Recall":[recall],
    "F1":[f1]
})
metrics_df.to_csv("nn_model_metrics_biomarker.csv", index=False)

cm = confusion_matrix(y_test, preds)
report = classification_report(y_test, preds)

print("\n===== Test Results =====")
print("AUC:", round(auc,4))
print("Accuracy:", round(acc,4))
print("Precision:", round(precision,4))
print("Recall:", round(recall,4))
print("F1 Score:", round(f1,4))
print("\nConfusion Matrix:\n", cm)
print("\nClassification Report:\n", report)

fpr, tpr, _ = roc_curve(y_test, probs)
plt.figure()
plt.plot(fpr, tpr, label=f"AUC={auc:.3f}")
plt.plot([0,1], [0,1], "--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve - Neural Network")
plt.legend()
plt.savefig("nn_roc_curve_biomarker.png", dpi=300)
plt.close()

print("ROC curve saved")


results = pd.DataFrame({
    "probability": probs.flatten(),
    "prediction": preds.flatten(),
    "true": y_test.values
})
results.to_csv("nn_predictions_biomarker.csv", index=False)