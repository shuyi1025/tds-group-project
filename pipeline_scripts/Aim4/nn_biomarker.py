print("script initiated")

import os
import json
import random
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim

from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import StratifiedKFold, ParameterSampler
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import (
    roc_auc_score, roc_curve, accuracy_score, confusion_matrix,
    precision_score, recall_score, f1_score, classification_report
)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# settings

seed = 42
outcome = "cvd_event"
eid = "eid"

# input data
train_path = "../../pipeline_outputs/aim2_3_output/final_datasets/train_ee_bio_stable_allclusters.csv"
test_path = "../../pipeline_outputs/aim2_3_output/final_datasets/test_ee_bio_stable_allclusters.csv"

# output folders
output_dir = Path("../../pipeline_outputs/aim4_output/NN_outputs")
output_dir.mkdir(parents=True, exist_ok=True)
auc_path = Path("../../pipeline_outputs/aim4_output/auc_overlay")
Path(auc_path).mkdir(parents=True, exist_ok=True)

# cv / tuning settings
n_splits = 3
n_iter = 30
max_epochs = 50
patience = 10
min_delta = 1e-4
num_workers = 0

print("settings defined")

# reproducibility

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


set_seed(seed)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("using device:", device)

# utilities

def sparse_to_tensor(x, dtype=torch.float32):
    """
    Convert sparse or dense matrix to a PyTorch tensor
    """
    if hasattr(x, "toarray"):
        x = x.toarray()
    return torch.tensor(x, dtype=dtype)


class early_stopping:
    """
    Stop training when validation AUC stops improving.
    """
    def __init__(self, patience=10, min_delta=0.0, mode="max"):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_score = None
        self.counter = 0
        self.best_state_dict = None
        self.best_epoch = 0
        self.should_stop = False

    def step(self, score, model, epoch):
        if self.best_score is None:
            improved = True
        else:
            if self.mode == "max":
                improved = score > (self.best_score + self.min_delta)
            else:
                improved = score < (self.best_score - self.min_delta)

        if improved:
            self.best_score = score
            self.counter = 0
            self.best_state_dict = deepcopy(model.state_dict())
            self.best_epoch = epoch
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True


class ukbn(nn.Module):
    """
    Feedforward neural network for binary classification.
    hidden_sizes controls the hidden-layer structure.
    """
    def __init__(self, input_dim, hidden_sizes=(128, 64), dropout=0.3):
        super().__init__()
        layers = []
        prev_dim = input_dim

        for h in hidden_sizes:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.BatchNorm1d(h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = h

        layers.append(nn.Linear(prev_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def build_preprocessor(x_df):
    """
    Scale numeric variables and one-hot encode categorical variables.
    """
    numeric_cols = x_df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    cat_cols = x_df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
    ])

    return preprocessor


def make_loaders(x_train, y_train, x_val, y_val, batch_size):
    """
    Create DataLoaders for training and validation.
    """
    x_train_t = sparse_to_tensor(x_train)
    x_val_t = sparse_to_tensor(x_val)

    y_train_t = torch.tensor(np.asarray(y_train), dtype=torch.float32).view(-1, 1)
    y_val_t = torch.tensor(np.asarray(y_val), dtype=torch.float32).view(-1, 1)

    train_ds = TensorDataset(x_train_t, y_train_t)
    val_ds = TensorDataset(x_val_t, y_val_t)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )

    return train_loader, val_loader, y_train_t


def make_train_test_loaders(x_train, y_train, x_test, y_test, batch_size):
    """
    Create DataLoaders for final train/test run.
    """
    x_train_t = sparse_to_tensor(x_train)
    x_test_t = sparse_to_tensor(x_test)

    y_train_t = torch.tensor(np.asarray(y_train), dtype=torch.float32).view(-1, 1)
    y_test_t = torch.tensor(np.asarray(y_test), dtype=torch.float32).view(-1, 1)

    train_ds = TensorDataset(x_train_t, y_train_t)
    test_ds = TensorDataset(x_test_t, y_test_t)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )

    return train_loader, test_loader, y_train_t, y_test_t


def train_one_fold(x_train_df, y_train, x_val_df, y_val, params):
    """
    Train one CV fold for one sampled hyperparameter combination.
    Preprocessing is fit only on fold-training data to avoid leakage.
    """
    preprocessor = build_preprocessor(x_train_df)
    x_train_proc = preprocessor.fit_transform(x_train_df)
    x_val_proc = preprocessor.transform(x_val_df)

    train_loader, val_loader, y_train_t = make_loaders(
        x_train_proc,
        y_train,
        x_val_proc,
        y_val,
        batch_size=params["batch_size"]
    )

    num_pos = y_train_t.sum().item()
    num_neg = y_train_t.shape[0] - num_pos
    pos_weight_value = num_neg / max(num_pos, 1.0)
    pos_weight = torch.tensor([pos_weight_value], dtype=torch.float32, device=device)

    model = ukbn(
        input_dim=x_train_proc.shape[1],
        hidden_sizes=params["hidden_sizes"],
        dropout=params["dropout"]
    ).to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    optimizer = optim.Adam(
        model.parameters(),
        lr=params["lr"],
        weight_decay=params["weight_decay"]
    )

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=2,
        threshold=min_delta
    )

    stopper = early_stopping(
        patience=patience,
        min_delta=min_delta,
        mode="max"
    )

    history = {
        "train_loss": [],
        "val_auc": [],
        "lr": []
    }

    for epoch in range(1, params["max_epochs"] + 1):
        model.train()
        running_loss = 0.0
        n_train = 0

        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)

            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()

            batch_n = yb.size(0)
            running_loss += loss.item() * batch_n
            n_train += batch_n

        avg_train_loss = running_loss / n_train
        history["train_loss"].append(avg_train_loss)
        history["lr"].append(optimizer.param_groups[0]["lr"])

        model.eval()
        val_probs = []
        val_true = []

        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device)
                logits = model(xb)
                probs = torch.sigmoid(logits).cpu().numpy().flatten()
                val_probs.extend(probs)
                val_true.extend(yb.numpy().flatten())

        val_auc = roc_auc_score(val_true, val_probs)
        history["val_auc"].append(val_auc)

        scheduler.step(val_auc)
        stopper.step(val_auc, model, epoch)

        if stopper.should_stop:
            break

    model.load_state_dict(stopper.best_state_dict)

    return {
        "best_val_auc": stopper.best_score,
        "best_epoch": stopper.best_epoch,
        "history": history
    }


def fit_final_model(x_train_df, y_train, x_test_df, y_test, best_params):
    """
    Fit final model on the full training set using the best hyperparameters,
    then evaluate on the untouched test set.
    """
    preprocessor = build_preprocessor(x_train_df)
    x_train_proc = preprocessor.fit_transform(x_train_df)
    x_test_proc = preprocessor.transform(x_test_df)

    train_loader, test_loader, y_train_t, _ = make_train_test_loaders(
        x_train_proc,
        y_train,
        x_test_proc,
        y_test,
        batch_size=best_params["batch_size"]
    )

    num_pos = y_train_t.sum().item()
    num_neg = y_train_t.shape[0] - num_pos
    pos_weight = torch.tensor([num_neg / max(num_pos, 1.0)], dtype=torch.float32).to(device)

    model = ukbn(
        input_dim=x_train_proc.shape[1],
        hidden_sizes=tuple(best_params["hidden_sizes"]),
        dropout=best_params["dropout"]
    ).to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = optim.Adam(
        model.parameters(),
        lr=best_params["lr"],
        weight_decay=best_params["weight_decay"]
    )

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=2,
        threshold=min_delta
    )

    n_epochs = int(best_params["chosen_epochs"])
    if n_epochs < 1:
        n_epochs = int(best_params["max_epochs"])

    print("setup complete")
    print(f"final training epochs: {n_epochs}")

    train_losses = []

    for epoch in range(n_epochs):
        model.train()
        epoch_loss = 0.0

        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)

            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        train_losses.append(epoch_loss)

        # optional scheduler step using training loss proxy here because
        # there is no held-out validation set during final full-train fit
        scheduler.step(-epoch_loss)

        print(f"epoch {epoch + 1}/{n_epochs} loss: {epoch_loss:.4f}")

    print("train complete")

    # save training loss curve
    plt.figure()
    plt.plot(train_losses)
    plt.xlabel("Epoch")
    plt.ylabel("Training Loss")
    plt.title("Neural Network Training Loss")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "nn_biomarker_training_loss.png"), dpi=300)
    plt.close()

    print("training curve saved")

    # test evaluation
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

    return model, preprocessor, probs, preds, train_losses


def main():
    
    # load data
  
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)

    x = train.drop(columns=[outcome, eid])
    y = train[outcome].astype(int)

    x_test = test.drop(columns=[outcome, eid])
    y_test = test[outcome].astype(int)

    print("training data loaded:", x.shape)
    print("test data loaded:", x_test.shape)
    print("raw input feature count:", x.shape[1])

   
    # hyperparameter search space

    param_dist = {
        "hidden_sizes": [
            (32,),
            (64,),
            (128,),
            (256,),
            (256, 128),
            (256, 64),
            (256, 128, 64),
        ],
        "dropout": [0.1, 0.2, 0.3],
        "lr": [1e-4, 1e-3, 1e-2, 5e-3],
        "batch_size": [64, 128],
        "weight_decay": [0.0, 1e-4],
        "max_epochs": [50],
    }

    sampled_params = list(ParameterSampler(param_dist, n_iter=n_iter, random_state=seed))
    print(f"randomly sampled hyperparameter combinations: {len(sampled_params)}")

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    all_results = []

   
    # tuning loop

    for combo_idx, params in enumerate(sampled_params, start=1):
        print(f"\n===== combination {combo_idx}/{len(sampled_params)} =====")
        print(params)

        fold_aucs = []
        fold_best_epochs = []

        for fold, (tr_idx, val_idx) in enumerate(skf.split(x, y), start=1):
            print(f"  fold {fold}/{n_splits}")

            x_tr = x.iloc[tr_idx].copy()
            y_tr = y.iloc[tr_idx].copy()
            x_val = x.iloc[val_idx].copy()
            y_val = y.iloc[val_idx].copy()

            fold_result = train_one_fold(x_tr, y_tr, x_val, y_val, params)

            fold_aucs.append(fold_result["best_val_auc"])
            fold_best_epochs.append(fold_result["best_epoch"])

            print(
                f"    best fold auc: {fold_result['best_val_auc']:.4f} "
                f"at epoch {fold_result['best_epoch']}"
            )

        result_row = {
            "hidden_sizes": list(params["hidden_sizes"]),
            "dropout": params["dropout"],
            "lr": params["lr"],
            "batch_size": params["batch_size"],
            "weight_decay": params["weight_decay"],
            "max_epochs": params["max_epochs"],
            "mean_cv_auc": float(np.mean(fold_aucs)),
            "std_cv_auc": float(np.std(fold_aucs)),
            "mean_best_epoch": int(np.round(np.mean(fold_best_epochs))),
            "min_best_epoch": int(np.min(fold_best_epochs)),
            "max_best_epoch": int(np.max(fold_best_epochs))
        }
        all_results.append(result_row)

 
    # save tuning outputs

    results_df = pd.DataFrame(all_results).sort_values(
        by=["mean_cv_auc", "std_cv_auc"],
        ascending=[False, True]
    ).reset_index(drop=True)

    results_df.to_csv(
        output_dir / "nn_biomarker_hyperparameter_search_results.csv",
        index=False
    )

    results_df.head(10).to_csv(
        output_dir / "nn_biomarker_hyperparameter_top10.csv",
        index=False
    )

    print("\ntop 10 combinations:")
    print(results_df.head(10))

    best_row = results_df.iloc[0].to_dict()

    best_params = {
        "hidden_sizes": best_row["hidden_sizes"],
        "dropout": float(best_row["dropout"]),
        "lr": float(best_row["lr"]),
        "batch_size": int(best_row["batch_size"]),
        "weight_decay": float(best_row["weight_decay"]),
        "max_epochs": int(best_row["max_epochs"]),
        "chosen_epochs": int(best_row["mean_best_epoch"]),
        "mean_cv_auc": float(best_row["mean_cv_auc"]),
        "std_cv_auc": float(best_row["std_cv_auc"])
    }

    with open(output_dir / "best_nn_params_ee.json", "w") as f:
        json.dump(best_params, f, indent=4)

    print("\nbest parameters saved:")
    print(json.dumps(best_params, indent=4))

    # tuning summary plot
    top_n = min(15, len(results_df))
    plt.figure(figsize=(10, 5))
    plt.plot(
        range(1, top_n + 1),
        results_df.loc[:top_n - 1, "mean_cv_auc"].values,
        marker="o"
    )
    plt.xlabel("ranked hyperparameter combination")
    plt.ylabel("mean cv auc")
    plt.title("top hyperparameter combinations by mean cv auc")
    plt.tight_layout()
    plt.savefig(output_dir / "nn_biomarker_hyperparameter_ranking.png", dpi=300)
    plt.close()

    print("tuning complete.")

    # final train on full train set + test evaluation

    model, preprocessor, probs, preds, train_losses = fit_final_model(
        x_train_df=x,
        y_train=y,
        x_test_df=x_test,
        y_test=y_test,
        best_params=best_params
    )

    # compute metrics
    auc = roc_auc_score(y_test, probs)
    acc = accuracy_score(y_test, preds)
    precision = precision_score(y_test, preds, zero_division=0)
    recall = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)

    metrics_df = pd.DataFrame({
        "AUC": [auc],
        "Accuracy": [acc],
        "Precision": [precision],
        "Recall": [recall],
        "F1": [f1]
    })
    metrics_df.to_csv(os.path.join(output_dir, "nn_biomarker_metrics.csv"), index=False)

    cm = confusion_matrix(y_test, preds)
    report = classification_report(y_test, preds, zero_division=0)

    print("\n===== NN Baseline + EE + Biomarker test results =====")
    print("AUC:", round(auc, 4))
    print("Accuracy:", round(acc, 4))
    print("Precision:", round(precision, 4))
    print("Recall:", round(recall, 4))
    print("F1 Score:", round(f1, 4))
    print("\nConfusion Matrix:\n", cm)
    print("\nClassification Report:\n", report)

    result_path = os.path.join(output_dir, "nn_biomarker_results.txt")
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("===== Neural Network Baseline + EE + Biomarker Test Performance =====\n")
        f.write(f"Accuracy:  {acc:.4f}\n")
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall:    {recall:.4f}\n")
        f.write(f"F1:        {f1:.4f}\n")
        f.write(f"AUC:       {auc:.4f}\n\n")
        f.write("Confusion Matrix:\n")
        f.write(np.array2string(cm))
        f.write("\n\nClassification Report:\n")
        f.write(report)

    print(f"results saved to: {result_path}")

    # roc curve
    fpr, tpr, _ = roc_curve(y_test, probs)
    plt.figure()
    plt.plot(fpr, tpr, label=f"AUC={auc:.3f}")
    plt.plot([0, 1], [0, 1], "--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - Neural Network")
    plt.legend()
    plt.tight_layout()

    roc_path = os.path.join(output_dir, "nn_biomarker_curve.png")
    plt.savefig(roc_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"ROC curve saved to: {roc_path}")

    # predictions
    results = pd.DataFrame({
        "probability": probs.flatten(),
        "prediction": preds.flatten(),
        "true": y_test.values
    })
    results.to_csv(os.path.join(output_dir, "nn_biomarker_predictions.csv"), index=False)
    print("nn ee predictions saved")

    # roc overlay file
    df = pd.DataFrame({
        "y_true": y_test,
        "y_pred": probs
    })
    df.to_csv(os.path.join(auc_path, "nn_baseline_ee_biomarker.csv"), index=False)
    print("roc overlay results saved")

    # optional save of model + preprocessor
    torch.save(model.state_dict(), os.path.join(output_dir, "nn_biomarker_model_state_dict.pt"))
    print("model state dict saved")

    print(f"all results saved to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
