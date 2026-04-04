import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle

df = pd.read_csv("loan.csv")

df = df.dropna()

y = df["Loan_Status"]
X = df.drop("Loan_Status", axis=1)

X = pd.get_dummies(X)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)

pickle.dump(model, open("model.pkl", "wb"))

print("Model trained successfully 🚀")