from flask import Flask, request, render_template
import pickle
import numpy as np

app = Flask(__name__)

# Model load karo
model = pickle.load(open('model.pkl', 'rb'))

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Form se data lena
        income = float(request.form['income'])
        loan_amount = float(request.form['loan_amount'])
        credit_score = float(request.form['credit_score'])

        # Model input
        features = np.array([[income, loan_amount, credit_score]])

        # Prediction
        prediction = model.predict(features)

        # Result
        if prediction[0] == 1:
            result = "Loan Approved ✅"
        else:
            result = "Loan Rejected ❌"

        return render_template('index.html', prediction_text=result)

    except Exception as e:
        return f"Error: {str(e)}"

# Run app
if __name__ == "__main__":
    app.run(debug=True)