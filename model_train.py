import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier

# LOAD DATA
df = pd.read_csv("loan.csv")
df.columns = df.columns.str.strip()

# CLEAN TEXT
for col in df.select_dtypes(include=["object"]):
    df[col] = df[col].astype(str).str.strip().str.lower()

# TARGET
df["loan_status"] = df["loan_status"].map({
    "approved": 1,
    "rejected": 0
})

df = df.dropna(subset=["loan_status"])
df["loan_status"] = df["loan_status"].astype(int)

# FEATURES ENCODING
df["education"] = df["education"].map({
    "graduate": 1,
    "not graduate": 0
})

df["self_employed"] = df["self_employed"].map({
    "yes": 1,
    "no": 0
})

# ⚡ SIMPLE BALANCE (IMPORTANT FIX)
approved = df[df.loan_status == 1]
rejected = df[df.loan_status == 0]

min_len = min(len(approved), len(rejected))

approved = approved.sample(min_len, random_state=42)
rejected = rejected.sample(min_len, random_state=42)

df = pd.concat([approved, rejected])

# FEATURES
features = [
    "income_annum",
    "loan_amount",
    "cibil_score",
    "education",
    "self_employed"
]

X = df[features].fillna(0)
y = df["loan_status"]

# SAVE FEATURES
pickle.dump(features, open("model_columns.pkl", "wb"))

# 🔥 STRONG MODEL
model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced"
)

model.fit(X, y)

pickle.dump(model, open("model.pkl", "wb"))

print("MODEL TRAINED SUCCESSFULLY 🚀 (BALANCED READY)")