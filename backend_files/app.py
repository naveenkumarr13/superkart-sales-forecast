import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify

# Initialize the Flask application
superkart_api = Flask("SuperKart Sales Predictor")

# Load the trained model pipeline (preprocessing + regressor)
model = joblib.load("superkart_model.joblib")

# Features expected by the model, in training order
FEATURES = [
    "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
    "Store_Size", "Store_Location_City_Type", "Store_Type",
    "Product_Id_char", "Store_Age_Years", "Product_Type_Category",
]


@superkart_api.get("/")
def home():
    """Health check endpoint."""
    return "Welcome to the SuperKart Sales Forecasting API!"


@superkart_api.post("/v1/predict")
def predict_sales():
    """Predict sales for a single product-store record sent as JSON."""
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Request body must be JSON."}), 400

    missing = [f for f in FEATURES if f not in data]
    if missing:
        return jsonify({"error": f"Missing features: {missing}"}), 400

    sample = pd.DataFrame([{f: data[f] for f in FEATURES}])
    prediction = model.predict(sample)[0]
    return jsonify({"Predicted_Sales": round(float(prediction), 2)})


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """Predict sales for every row of an uploaded CSV file."""
    if "file" not in request.files:
        return jsonify({"error": "Upload a CSV file under the key 'file'."}), 400

    input_data = pd.read_csv(request.files["file"])

    missing = [f for f in FEATURES if f not in input_data.columns]
    if missing:
        return jsonify({"error": f"Missing columns: {missing}"}), 400

    predictions = model.predict(input_data[FEATURES])
    output = {str(idx): round(float(pred), 2) for idx, pred in zip(input_data.index, predictions)}
    return jsonify(output)


if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=7860, debug=False)
