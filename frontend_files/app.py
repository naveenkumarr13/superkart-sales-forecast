import os
import requests
import pandas as pd
import streamlit as st

# Backend URL: inside the Docker network the backend container is reachable by its name
BACKEND_URL = os.getenv("BACKEND_URL", "http://superkart-backend:7860")

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒")
st.title("SuperKart Sales Forecast")
st.write("Predict the total sales revenue of a product in a store.")

PERISHABLES = ["Dairy", "Meat", "Fruits and Vegetables", "Breakfast", "Breads", "Seafood"]
PRODUCT_TYPES = ["Fruits and Vegetables", "Snack Foods", "Frozen Foods", "Dairy", "Household",
                 "Baking Goods", "Canned", "Health and Hygiene", "Meat", "Soft Drinks", "Breads",
                 "Hard Drinks", "Others", "Starchy Foods", "Breakfast", "Seafood"]

# ---------------- Online prediction ----------------
st.subheader("Online prediction")

col1, col2 = st.columns(2)
with col1:
    product_id_char = st.selectbox("Product ID prefix", ["FD", "NC", "DR"],
                                   help="FD = Food, NC = Non-consumable, DR = Drinks")
    product_type = st.selectbox("Product Type", PRODUCT_TYPES)
    product_weight = st.number_input("Product Weight", min_value=0.0, max_value=50.0, value=12.66)
    product_sugar = st.selectbox("Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"])
    product_area = st.number_input("Product Allocated Area (ratio)", min_value=0.0, max_value=1.0,
                                   value=0.027, step=0.001, format="%.3f")
    product_mrp = st.number_input("Product MRP", min_value=0.0, max_value=500.0, value=117.08)
with col2:
    store_year = st.number_input("Store Establishment Year", min_value=1950, max_value=2025,
                                 value=2009, step=1)
    store_size = st.selectbox("Store Size", ["Small", "Medium", "High"], index=1)
    store_city = st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"], index=1)
    store_type = st.selectbox("Store Type", ["Supermarket Type2", "Supermarket Type1",
                                             "Departmental Store", "Food Mart"])

payload = {
    "Product_Weight": product_weight,
    "Product_Sugar_Content": product_sugar,
    "Product_Allocated_Area": product_area,
    "Product_MRP": product_mrp,
    "Store_Size": store_size,
    "Store_Location_City_Type": store_city,
    "Store_Type": store_type,
    "Product_Id_char": product_id_char,
    "Store_Age_Years": 2025 - int(store_year),
    "Product_Type_Category": "Perishables" if product_type in PERISHABLES else "Non Perishables",
}

if st.button("Predict", type="primary"):
    try:
        response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
        if response.status_code == 200:
            prediction = response.json()["Predicted_Sales"]
            st.success(f"Predicted product-store sales: {prediction:,.2f}")
        else:
            st.error(f"Error from API ({response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the backend at {BACKEND_URL}: {e}")

# ---------------- Batch prediction ----------------
st.subheader("Batch prediction")
st.caption("Upload a CSV with the columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, "
           "Product_MRP, Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, "
           "Store_Age_Years, Product_Type_Category")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
if uploaded_file is not None and st.button("Predict batch"):
    try:
        response = requests.post(f"{BACKEND_URL}/v1/predictbatch",
                                 files={"file": uploaded_file.getvalue()}, timeout=60)
        if response.status_code == 200:
            preds = response.json()
            result = pd.read_csv(uploaded_file)
            result["Predicted_Sales"] = [preds[str(i)] for i in result.index]
            st.success(f"Predicted {len(result)} rows.")
            st.dataframe(result)
            st.download_button("Download predictions", result.to_csv(index=False),
                               file_name="superkart_predictions.csv", mime="text/csv")
        else:
            st.error(f"Error from API ({response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the backend at {BACKEND_URL}: {e}")
