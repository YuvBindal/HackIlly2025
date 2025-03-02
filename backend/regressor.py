import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor

# Create models directory if it doesn't exist
model_dir = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(model_dir, exist_ok=True)

# Load dataset
csv_path = "./model_development/side_by_side_metrics.csv"
df = pd.read_csv(csv_path)

# Select features and target
features = ["number_of_trades", "total_items_traded", "total_volume_usd", "total_fees_sol", "tx_count"]
target = "failed_tx_count"

# Data preprocessing
df = df[features + [target]].dropna()
X = df[features]
y = df[target]

# Scale features
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# Train-test split (using a larger test size due to small dataset)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.3, shuffle=False
)

# Initialize and train XGBoost model
model = XGBRegressor(
    n_estimators=50,  # Reduced from 100 due to smaller dataset
    learning_rate=0.1,
    max_depth=4,      # Reduced from 6 to prevent overfitting
    min_child_weight=1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)

# Train the model
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

# Save model and scaler
model_path = os.path.join(model_dir, "xgboost_model_V2.pkl")
scaler_path = os.path.join(model_dir, "scaler_side_by_side.pkl")

with open(model_path, 'wb') as file:
    pickle.dump(model, file)
print(f"\nModel saved at: {model_path}")

with open(scaler_path, 'wb') as file:
    pickle.dump(scaler, file)
print(f"Scaler saved at: {scaler_path}")

# Function to make predictions
def predict_failed_tx(new_data):
    """
    Make predictions using the saved model
    """
    with open(model_path, 'rb') as file:
        loaded_model = pickle.load(file)
    with open(scaler_path, 'rb') as file:
        loaded_scaler = pickle.load(file)
    
    input_df = pd.DataFrame([new_data])
    input_df = input_df[features]
    
    input_scaled = loaded_scaler.transform(input_df)
    prediction = loaded_model.predict(input_scaled)[0]
    
    return prediction

# Example usage
if __name__ == "__main__":
    test_data = {
        "number_of_trades": 5.0,
        "total_items_traded": 5.0,
        "total_volume_usd": 1000.0,
        "total_fees_sol": 2,
        "tx_count": 12300
    }
    result = predict_failed_tx(test_data)
    print(f"\nTest prediction for failed transactions: {result:.2f}")
    print(f"Predicted failure rate: ", max(0, result/test_data['tx_count']))

# # Plot feature importance
# plt.figure(figsize=(10, 6))
# importance = model.feature_importances_
# plt.bar(features, importance)
# plt.xticks(rotation=45)
# plt.title('Feature Importance in Predicting Failed Transactions')
# plt.tight_layout()
# plt.show()

# # Created/Modified files during execution:
# print("\nCreated/Modified files:")
# print(f"- {model_path}")
# print(f"- {scaler_path}")