import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import os
import pickle
from datetime import datetime

# Create models directory if it doesn't exist
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)

# Load dataset
csv_path = "./metrics_cache/combined_df.csv"
df = pd.read_csv(csv_path)

# Analyze the target variable
print("\nTarget variable statistics:")
print(df['avg_fee_sol'].describe())
print("\nUnique values in target variable:", len(df['avg_fee_sol'].unique()))
print("Min value:", df['avg_fee_sol'].min())
print("Max value:", df['avg_fee_sol'].max())

# Select features and target - now predicting avg_fee_sol
# Removed total_fees_sol as it might be too predictive
features = ["tps", "failed_tx_count", "tx_count", "total_volume_usd"]
target = "avg_fee_sol"

# Data preprocessing
df = df[features + [target]].dropna()

# Create meaningful derived features
df['congestion_ratio'] = df['failed_tx_count'] / df['tps'].where(df['tps'] > 0, 1)
df['tx_per_second'] = df['tx_count'] / 3600  # Assuming data is hourly
features.extend(['congestion_ratio', 'tx_per_second'])

# Check correlation with target
print("\nCorrelation with avg_fee_sol:")
correlations = df.corr()[target].sort_values(ascending=False)
print(correlations)

# Prepare features and target
X = df[features]
y = df[target]

# Scale features
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# Train-test split - using chronological split since this is time series data
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, shuffle=False
)

# Try a simple linear model first
linear_model = LinearRegression()
linear_model.fit(X_train, y_train)
linear_pred = linear_model.predict(X_test)

print("\nLinear model performance:")
print(f"R² Score: {r2_score(y_test, linear_pred):.4f}")
print(f"Mean Absolute Error: {mean_absolute_error(y_test, linear_pred):.8f}")

# Initialize and train XGBoost model with more aggressive parameters
model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.1,
    max_depth=9,
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
r2 = r2_score(y_test, y_pred)

print("\nTransaction Fee Prediction Model Performance:")
print(f"Mean Squared Error: {mse:.8f}")
print(f"Root Mean Squared Error: {rmse:.8f}")
print(f"Mean Absolute Error: {mae:.8f}")
print(f"R² Score: {r2:.4f}")

# Feature importance
plt.figure(figsize=(12, 6))
feature_importance = model.feature_importances_
sorted_idx = np.argsort(feature_importance)
plt.barh(range(len(sorted_idx)), feature_importance[sorted_idx])
plt.yticks(range(len(sorted_idx)), np.array(X.columns)[sorted_idx])
plt.title('Feature Importance for Transaction Fee Prediction')
plt.tight_layout()
plt.savefig(os.path.join(model_dir, 'feature_importance.png'))
print(f"Feature importance plot saved to {os.path.join(model_dir, 'feature_importance.png')}")

# Plot actual vs predicted
plt.figure(figsize=(12, 6))
plt.plot(y_test.values, label='Actual')
plt.plot(y_pred, label='Predicted')
plt.title('Actual vs Predicted Transaction Fees')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(model_dir, 'actual_vs_predicted.png'))
print(f"Actual vs Predicted plot saved to {os.path.join(model_dir, 'actual_vs_predicted.png')}")

# Save model, scaler, and feature list
model_path = os.path.join(model_dir, "fee_prediction_model.pkl")
scaler_path = os.path.join(model_dir, "fee_prediction_scaler.pkl")
features_path = os.path.join(model_dir, "fee_prediction_features.pkl")

with open(model_path, 'wb') as file:
    pickle.dump(model, file)
print(f"\nModel saved at: {model_path}")

with open(scaler_path, 'wb') as file:
    pickle.dump(scaler, file)
print(f"Scaler saved at: {scaler_path}")

with open(features_path, 'wb') as file:
    pickle.dump(features, file)
print(f"Feature list saved at: {features_path}")

# Function to predict transaction fees with debugging
def predict_transaction_fee(new_data, debug=False):
    """
    Make predictions for transaction fees using the saved model

    Parameters:
    -----------
    new_data : dict
        Dictionary containing current metrics (tps, failed_tx_count, tx_count, total_volume_usd)
    debug : bool
        Whether to print debugging information

    Returns:
    --------
    float
        Predicted average transaction fee in SOL
    """
    # Load model, scaler, and feature list
    with open(model_path, 'rb') as file:
        loaded_model = pickle.load(file)
    with open(scaler_path, 'rb') as file:
        loaded_scaler = pickle.load(file)
    with open(features_path, 'rb') as file:
        feature_list = pickle.load(file)

    # Create a DataFrame for the input
    input_df = pd.DataFrame([new_data])

    # Calculate derived features
    if 'tps' in input_df.columns and 'failed_tx_count' in input_df.columns:
        input_df['congestion_ratio'] = input_df['failed_tx_count'] / input_df['tps'].where(input_df['tps'] > 0, 1)

    if 'tx_count' in input_df.columns:
        input_df['tx_per_second'] = input_df['tx_count'] / 3600  # Assuming hourly data

    # Ensure all required features are present
    for feature in feature_list:
        if feature not in input_df.columns:
            input_df[feature] = 0  # Default value for missing features

    # Select only the features used during training
    input_df = input_df[feature_list]

    if debug:
        print("\nInput features:")
        print(input_df)

    # Scale input
    input_scaled = loaded_scaler.transform(input_df)

    if debug:
        print("\nScaled input:")
        print(input_scaled)

    # Make prediction
    prediction = loaded_model.predict(input_scaled)[0]

    if debug:
        print("\nRaw prediction:", prediction)

    # Also calculate using a simple rule-based approach for comparison
    base_fee = 0.000125  # Base fee in SOL
    congestion_factor = new_data['failed_tx_count'] / max(new_data['tx_count'], 1) * 10
    tps_factor = new_data['tps'] / 2000  # Normalize to a typical max TPS

    rule_based_fee = base_fee * (1 + congestion_factor) * (1 + tps_factor)

    if debug:
        print(f"\nRule-based fee: {rule_based_fee:.8f} SOL")

    return prediction

# Example usage
if __name__ == "__main__":
    # Example current data
    current_data = {
        "tps": 4000,
        "failed_tx_count": 500000,
        "tx_count": 1000,
        "total_volume_usd": 10000
    }

    # Predict transaction fee with debugging
    predicted_fee = predict_transaction_fee(current_data, debug=True)
    print(f"\nPredicted average transaction fee: {predicted_fee:.8f} SOL")

    # Predict fee for next 15 minutes with different TPS scenarios
    print("\nFee predictions for next 15 minutes under different scenarios:")

    # Create a range of congestion scenarios
    tps_values = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]

    for tps in tps_values:
        # Scale other metrics proportionally
        scenario = current_data.copy()
        scenario["tps"] = tps
        # Adjust failed transactions based on TPS (higher TPS often means more failures)
        scenario["failed_tx_count"] = int(tps * 0.05)  # 5% failure rate
        # Adjust tx_count based on TPS
        scenario["tx_count"] = int(tps * 3.5)  # Assuming each transaction stays in the mempool for ~3.5 seconds

        fee = predict_transaction_fee(scenario)
        print(f"Scenario (TPS={tps}, Failed={scenario['failed_tx_count']}): {fee:.8f} SOL")

    # Try extreme scenarios to test model sensitivity
    print("\nExtreme scenarios:")

    # Very low congestion
    low_scenario = current_data.copy()
    low_scenario["tps"] = 100
    low_scenario["failed_tx_count"] = 1
    low_scenario["tx_count"] = 350
    print(f"Very low congestion: {predict_transaction_fee(low_scenario):.8f} SOL")

    # Very high congestion
    high_scenario = current_data.copy()
    high_scenario["tps"] = 5000
    high_scenario["failed_tx_count"] = 1000
    high_scenario["tx_count"] = 17500
    print(f"Very high congestion: {predict_transaction_fee(high_scenario):.8f} SOL")