import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import os
model_dir = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(model_dir, exist_ok=True)

# 🔹 Load dataset
csv_path = "./metrics_cache/combined_df.csv"
df = pd.read_csv(csv_path)

# 🔹 Select features (inputs) and target (output)
features = ["tps", "avg_fee_sol", "total_fees_sol", "failed_tx_count", "tx_count"]
target = "failed_tx_count"  # Predicting congestion (failed transactions)

# 🔹 Drop missing values
df = df[features].dropna()

# 🔹 Normalize data using MinMaxScaler
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df)

# 🔹 Create sequences for LSTM
def create_sequences(data, target_index, seq_length=10):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i : i + seq_length])
        y.append(data[i + seq_length, target_index])
    return np.array(X), np.array(y)

SEQ_LENGTH = 10  # Time steps
X, y = create_sequences(df_scaled, target_index=df.columns.get_loc(target), seq_length=SEQ_LENGTH)

# 🔹 Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# 🔹 Print dataset shapes
print("✅ X_train shape:", X_train.shape)
print("✅ X_test shape:", X_test.shape)

# 🔹 Define LSTM model
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(SEQ_LENGTH, X.shape[2])),
    Dropout(0.2),
    LSTM(32, return_sequences=False),
    Dropout(0.2),
    Dense(16, activation="relu"),
    Dense(1, activation="linear")  # Regression output
])

# 🔹 Compile model
model.compile(optimizer="adam", loss="mse", metrics=["mae"])
model.summary()

# 🔹 Train the model
history = model.fit(X_train, y_train, epochs=50, batch_size=16, validation_data=(X_test, y_test))

# 🔹 Plot training loss
plt.plot(history.history['loss'], label="Train Loss")
plt.plot(history.history['val_loss'], label="Validation Loss")
plt.legend()
plt.title("LSTM Training Loss")
plt.show()

# 🔹 Make predictions
y_pred = model.predict(X_test)

# 🔹 Convert back to original scale
# Create a zero-filled array with the correct shape
y_test_reshaped = np.zeros((len(y_test), len(features)))
# Put the y_test values in the target column
y_test_reshaped[:, features.index(target)] = y_test
# Inverse transform
y_test_original = scaler.inverse_transform(y_test_reshaped)[:, features.index(target)]

# Do the same for predictions
y_pred_reshaped = np.zeros((len(y_pred), len(features)))
y_pred_reshaped[:, features.index(target)] = y_pred.flatten()
y_pred_original = scaler.inverse_transform(y_pred_reshaped)[:, features.index(target)]

# 🔹 Plot Actual vs Predicted values
plt.figure(figsize=(10, 5))
plt.plot(y_test_original, label="Actual", color='blue')
plt.plot(y_pred_original, label="Predicted", color='red', linestyle='dashed')
plt.legend()
plt.title("Actual vs Predicted Failed Transactions")
plt.show()

# �� Save trained model using pickle
# Save model
model_path = os.path.join(model_dir, "xgboost_model.pkl")
with open(model_path, 'wb') as file:
    pickle.dump(model, file)
print(f"✅ Model saved successfully at: {model_path}")

# Save scaler
scaler_path = os.path.join(model_dir, "scaler.pkl")
with open(scaler_path, 'wb') as file:
    pickle.dump(scaler, file)
print(f"✅ Scaler saved successfully at: {scaler_path}")

# Function to make predictions with the saved model
def predict_congestion(new_data):
    """
    Make predictions using the trained model
    new_data should be a dictionary with keys: ["tps", "avg_fee_sol", "total_fees_sol", "tx_count"]
    """
    # Load model and scaler if not already loaded
    if not hasattr(predict_congestion, 'model'):
        model_path = os.path.join(model_dir, "xgboost_model.pkl")
        scaler_path = os.path.join(model_dir, "scaler.pkl")
        
        with open(model_path, 'rb') as file:
            predict_congestion.model = pickle.load(file)
        with open(scaler_path, 'rb') as file:
            predict_congestion.scaler = pickle.load(file)
    
    # Convert input to DataFrame
    input_df = pd.DataFrame([new_data])
    
    # Ensure correct feature order
    input_df = input_df[["tps", "avg_fee_sol", "total_fees_sol", "tx_count"]]
    
    # Scale the input
    input_scaled = predict_congestion.scaler.transform(input_df)
    
    # Make prediction
    prediction = predict_congestion.model.predict(input_scaled)[0]
    
    return prediction
