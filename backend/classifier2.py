import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import os
import pickle

# Create models directory if it doesn't exist
model_dir = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(model_dir, exist_ok=True)

# Load dataset
csv_path = "./metrics_cache/combined_df.csv"
df = pd.read_csv(csv_path)

# Select features and target
features = ["tps", "avg_fee_sol", "total_fees_sol", "failed_tx_count", "tx_count"]
target = "failed_tx_count"

# Data preprocessing
df = df[features].dropna()
X = df.drop(target, axis=1)
y = df[target]

# Scale features
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, shuffle=False
)

# Initialize and train XGBoost model
model = XGBRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=6,
    min_child_weight=1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

# Train the model with correct parameters
model.fit(
    X_train, 
    y_train,
    eval_set=[(X_test, y_test)],
    verbose=True
)

# Make predictions and calculate metrics
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mse)

print("\nModel Performance Metrics:")
print(f"Mean Squared Error: {mse:.2f}")
print(f"Root Mean Squared Error: {rmse:.2f}")
print(f"Mean Absolute Error: {mae:.2f}")

# Save model and scaler using pickle
model_path = os.path.join(model_dir, "xgboost_model.pkl")
scaler_path = os.path.join(model_dir, "scaler.pkl")

with open(model_path, 'wb') as file:
    pickle.dump(model, file)
print(f"\nModel saved at: {model_path}")

with open(scaler_path, 'wb') as file:
    pickle.dump(scaler, file)
print(f"Scaler saved at: {scaler_path}")

# Function to load model and make predictions
def predict_congestion(new_data):
    """
    Make predictions using the saved model
    """
    # Load model and scaler
    with open(model_path, 'rb') as file:
        loaded_model = pickle.load(file)
    with open(scaler_path, 'rb') as file:
        loaded_scaler = pickle.load(file)
    
    # Prepare input data
    input_df = pd.DataFrame([new_data])
    input_df = input_df[["tps", "avg_fee_sol", "total_fees_sol", "tx_count"]]
    
    # Scale input
    input_scaled = loaded_scaler.transform(input_df)
    
    # Make prediction
    prediction = loaded_model.predict(input_scaled)[0]
    
    return prediction

# Example usage
if __name__ == "__main__":
    test_data = {
        "tps": 1000,
        "avg_fee_sol": 0.000001,
        "total_fees_sol": 0.1,
        "tx_count": 5000
    }
    result = predict_congestion(test_data)
    print(f"\nTest prediction: {result:.2f}")