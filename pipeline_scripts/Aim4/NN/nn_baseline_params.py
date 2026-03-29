# nn_hyperparameter_tuning.py

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
from sklearn.model_selection import StratifiedKFold, ParameterGrid
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import roc_auc_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt



# Settings

SEED = 42
OUTCOME = "cvd_event"
EID = "eid"

TRAIN_PATH = "/rds/general/project/hda_25-26/live/TDS/TDS_Group8/modelling/NN/train_baseline.csv"
OUTPUT_DIR = Path("/rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_outputs/aim4_output/NN_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N_SPLITS = 5
MAX_EPOCHS = 100
PATIENCE = 10
MIN_DELTA = 1e-4
NUM_WORKERS = 0



# Reproducibility

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


set_seed(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)



# Utilities

def sparse_to_tensor(x, dtype=torch.float32):
    """Convert sparse/dense matrix to PyTorch tensor."""
    if hasattr(x, "toarray"):
        x = x.toarray()
    return torch.tensor(x, dtype=dtype)


class EarlyStopping:
    def __init__(self, patience=10, min_delta=0.0, mode="max"):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_score = None
        self.counter = 0
        self.best_state_dict = None
        self.should_stop = False
        self.best_epoch = 0

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


class UKBN(nn.Module):
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


def build_preprocessor(X_df):
    numeric_cols = X_df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    cat_cols = X_df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
    ])

    return preprocessor


def make_loaders(X_train, y_train, X_val, y_val, batch_size):
    X_train_t = sparse_to_tensor(X_train)
    X_val_t = sparse_to_tensor(X_val)
    y_train_t = torch.tensor(np.asarray(y_train), dtype=torch.float32).view(-1, 1)
    y_val_t = torch.tensor(np.asarray(y_val), dtype=torch.float32).view(-1, 1)

    train_ds = TensorDataset(X_train_t, y_train_t)
    val_ds = TensorDataset(X_val_t, y_val_t)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, num_workers=NUM_WORKERS
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, num_workers=NUM_WORKERS
    )

    return train_loader, val_loader, y_train_t


def train_one_fold(X_train_df, y_train, X_val_df, y_val, params):
    preprocessor = build_preprocessor(X_train_df)
    X_train_proc = preprocessor.fit_transform(X_train_df)
    X_val_proc = preprocessor.transform(X_val_df)

    train_loader, val_loader, y_train_t = make_loaders(
        X_train_proc, y_train, X_val_proc, y_val, batch_size=params["batch_size"]
    )

    # class imbalance handling
    num_pos = y_train_t.sum().item()
    num_neg = y_train_t.shape[0] - num_pos
    pos_weight_value = num_neg / max(num_pos, 1.0)
    pos_weight = torch.tensor([pos_weight_value], dtype=torch.float32, device=device)

    model = UKBN(
        input_dim=X_train_proc.shape[1],
        hidden_sizes=params["hidden_sizes"],
        dropout=params["dropout"]
    ).to(device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    optimizer = optim.Adam(
        model.parameters(),
        lr=params["learning_rate"]
    )

    early_stopper = EarlyStopping(
        patience=PATIENCE,
        min_delta=MIN_DELTA,
        mode="max"
    )

    history = {
        "train_loss": [],
        "val_auc": []
    }

    for epoch in range(1, MAX_EPOCHS + 1):
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

        early_stopper.step(val_auc, model, epoch)

        if early_stopper.should_stop:
            break

    model.load_state_dict(early_stopper.best_state_dict)

    return {
        "best_val_auc": early_stopper.best_score,
        "best_epoch": early_stopper.best_epoch,
        "history": history
    }


def main():
    train = pd.read_csv(TRAIN_PATH)

    X = train.drop(columns=[OUTCOME, EID])
    y = train[OUTCOME].astype(int)

    print("Training data loaded:", X.shape)

   
    # Parameter grid
 
    param_grid = {
        "hidden_sizes": [
            (32,),
            (64,),
            (128,),
            (128, 64),
            (256, 128)
        ],
        "dropout": [0.1, 0.2, 0.3],
        "learning_rate": [1e-4, 1e-3, 5e-3, 1e-2, 5e-2],
        "batch_size": [64, 128]
    }

    grid = list(ParameterGrid(param_grid))
    print(f"Total hyperparameter combinations: {len(grid)}")

    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

    all_results = []

    for combo_idx, params in enumerate(grid, start=1):
        print(f"\n===== Combination {combo_idx}/{len(grid)} =====")
        print(params)

        fold_aucs = []
        fold_best_epochs = []

        for fold, (tr_idx, val_idx) in enumerate(skf.split(X, y), start=1):
            print(f"  Fold {fold}/{N_SPLITS}")

            X_tr = X.iloc[tr_idx].copy()
            y_tr = y.iloc[tr_idx].copy()
            X_val = X.iloc[val_idx].copy()
            y_val = y.iloc[val_idx].copy()

            fold_result = train_one_fold(X_tr, y_tr, X_val, y_val, params)

            fold_aucs.append(fold_result["best_val_auc"])
            fold_best_epochs.append(fold_result["best_epoch"])

            print(
                f"    Best fold AUC: {fold_result['best_val_auc']:.4f} "
                f"at epoch {fold_result['best_epoch']}"
            )

        result_row = {
            **params,
            "mean_cv_auc": float(np.mean(fold_aucs)),
            "std_cv_auc": float(np.std(fold_aucs)),
            "mean_best_epoch": int(np.round(np.mean(fold_best_epochs))),
            "min_best_epoch": int(np.min(fold_best_epochs)),
            "max_best_epoch": int(np.max(fold_best_epochs))
        }
        all_results.append(result_row)

    results_df = pd.DataFrame(all_results).sort_values(
        by=["mean_cv_auc", "std_cv_auc"],
        ascending=[False, True]
    ).reset_index(drop=True)

    # save full search results
    results_csv = OUTPUT_DIR / "nn_hyperparameter_search_results.csv"
    results_df.to_csv(results_csv, index=False)

    print("\nTop 10 combinations:")
    print(results_df.head(10))

    # save top 10 separately
    results_df.head(10).to_csv(
        OUTPUT_DIR / "nn_hyperparameter_top10.csv",
        index=False
    )

    best_row = results_df.iloc[0].to_dict()

    best_params = {
        "hidden_sizes": list(best_row["hidden_sizes"]),
        "dropout": float(best_row["dropout"]),
        "learning_rate": float(best_row["learning_rate"]),
        "batch_size": int(best_row["batch_size"]),
        "chosen_epochs": int(best_row["mean_best_epoch"]),
        "mean_cv_auc": float(best_row["mean_cv_auc"]),
        "std_cv_auc": float(best_row["std_cv_auc"])
    }

    # save best params
    best_params_path = OUTPUT_DIR / "best_nn_params_baseline.json"
    with open(best_params_path, "w") as f:
        json.dump(best_params, f, indent=4)

    print("\nBest parameters saved to:", best_params_path)
    print(json.dumps(best_params, indent=4))

    # plot top 15 AUCs
    top_n = min(15, len(results_df))
    plt.figure(figsize=(10, 5))
    plt.plot(
        range(1, top_n + 1),
        results_df.loc[:top_n - 1, "mean_cv_auc"].values,
        marker="o"
    )
    plt.xlabel("Ranked hyperparameter combination")
    plt.ylabel("Mean CV AUC")
    plt.title("Top Hyperparameter Combinations by Mean CV AUC")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "nn_hyperparameter_ranking.png", dpi=300)
    plt.close()

    print("Tuning complete.")
    print(f"Results saved to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
