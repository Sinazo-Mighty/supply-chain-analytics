"""
Step 4: predict whether an order line will be delivered late.
Run from the repo root:  py -3.13 scripts/04_train_model.py
Needs:  py -3.13 -m pip install scikit-learn pandas

Design choices (explain these in your README):
- Only features known AT ORDER TIME are used. Anything that happens after
  shipping (actual days, delivery status, shipping date, order status) would
  leak the answer, so it is excluded.
- Cancelled shipments are excluded (they can't be late), and so is data after
  Sep 2017, where the dataset changes shape.
- The split is by time: train on the earlier orders, test on the later ones,
  like real forecasting.
- Results are compared with two baselines: always guessing the majority class,
  and a model that only knows the shipping mode.
"""
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

P = Path("data/processed")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

fact = pd.read_csv(P / "fact_order_item.csv", parse_dates=["order_date"])
loc = pd.read_csv(P / "dim_location.csv")
prod = pd.read_csv(P / "dim_product.csv")
cust = pd.read_csv(P / "dim_customer.csv")

df = (fact.merge(loc, on="location_key")
          .merge(prod[["product_card_id", "department_name"]], on="product_card_id")
          .merge(cust[["customer_id", "customer_segment"]], on="customer_id"))

df = df[(df["delivery_status"] != "Shipping canceled") & (df["order_date"] < "2017-10-01")].copy()
df["order_month"] = df["order_date"].dt.month
df["order_dow"] = df["order_date"].dt.dayofweek
df["order_hour"] = df["order_date"].dt.hour

CATEGORICAL = ["shipping_mode", "market", "order_region", "department_name", "customer_segment"]
NUMERIC = ["quantity", "unit_price", "discount_rate", "order_month", "order_dow", "order_hour"]
FEATURES = CATEGORICAL + NUMERIC
TARGET = "is_late"

train = df[df["order_date"] < "2017-04-01"]
test = df[df["order_date"] >= "2017-04-01"]
print(f"Train: {len(train):,} lines | Test: {len(test):,} lines | late rate in test: {test[TARGET].mean():.1%}")


def make_model(cat_cols, num_cols):
    pre = ColumnTransformer(
        [("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), cat_cols)],
        remainder="passthrough",
    )
    # Tell the model which columns are categorical (the first len(cat_cols) after preprocessing).
    clf = HistGradientBoostingClassifier(
        categorical_features=list(range(len(cat_cols))), random_state=42)
    return Pipeline([("pre", pre), ("clf", clf)])


def evaluate(name, cat_cols, num_cols):
    cols = cat_cols + num_cols
    model = make_model(cat_cols, num_cols).fit(train[cols], train[TARGET])
    proba = model.predict_proba(test[cols])[:, 1]
    return model, {
        "model": name,
        "accuracy": round(accuracy_score(test[TARGET], proba > 0.5), 3),
        "roc_auc": round(roc_auc_score(test[TARGET], proba), 3),
    }


majority = max(test[TARGET].mean(), 1 - test[TARGET].mean())
results = [{"model": "Always guess the majority class", "accuracy": round(majority, 3), "roc_auc": 0.5}]
_, r = evaluate("Shipping mode only", ["shipping_mode"], []); results.append(r)
full_model, r = evaluate("All order-time features", CATEGORICAL, NUMERIC); results.append(r)

res = pd.DataFrame(results)
res.to_csv(REPORTS / "model_results.csv", index=False)
print("\n", res.to_string(index=False))

# Which features matter? (drop in ROC-AUC when a feature is shuffled)
imp = permutation_importance(full_model, test[FEATURES], test[TARGET],
                             scoring="roc_auc", n_repeats=5, random_state=42)
imp_df = (pd.DataFrame({"feature": FEATURES, "importance": imp.importances_mean.round(4)})
          .sort_values("importance", ascending=False))
imp_df.to_csv(REPORTS / "model_feature_importance.csv", index=False)
print("\nFeature importance (drop in ROC-AUC when shuffled):")
print(imp_df.to_string(index=False))
