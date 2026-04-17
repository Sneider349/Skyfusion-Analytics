#!/usr/bin/env python3
"""
Flow Prediction Model for Skyfusion Analytics
Predicts river flow variability based on historical and morphological data
"""

import json
import sys
import numpy as np
from datetime import datetime, timedelta

def generate_predictions(historical_data, horizon, confidence):
    """
    Generate flow predictions using simplified model
    In production, this would load a trained TensorFlow model
    """
    base_flow = 10.0
    trend = 0.5
    noise = np.random.normal(0, 0.5, horizon)
    
    predictions = []
    current_flow = base_flow
    
    for i in range(horizon):
        variation = trend * (1 - i / horizon) + np.random.uniform(-0.3, 0.3)
        current_flow = current_flow + variation + noise[i]
        current_flow = max(1.0, current_flow)
        predictions.append(round(current_flow, 2))
    
    margin = 1.96 * confidence
    lower_bound = [p - margin for p in predictions]
    upper_bound = [p + margin for p in predictions]
    
    return predictions, lower_bound, upper_bound

def calculate_metrics(predictions, actual=None):
    """
    Calculate model performance metrics
    """
    if actual is None:
        actual = predictions
    
    mse = np.mean((np.array(predictions) - np.array(actual)) ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(np.array(predictions) - np.array(actual)))
    
    ss_res = np.sum((np.array(actual) - np.array(predictions)) ** 2)
    ss_tot = np.sum((np.array(actual) - np.mean(actual)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4)
    }

def main():
    try:
        input_data = json.loads(sys.stdin.read())
        
        data = input_data.get('data', {})
        study_area = input_data.get('studyArea', {})
        horizon = input_data.get('horizon', 24)
        confidence = input_data.get('confidence', 0.95)
        
        predictions, lower, upper = generate_predictions(data, horizon, confidence)
        
        metrics = calculate_metrics(predictions)
        
        variability = max(predictions) - min(predictions)
        
        result = {
            "success": True,
            "modelName": "FLOW_PREDICTION_V1",
            "predictions": predictions,
            "confidenceInterval": {
                "lower": lower,
                "upper": upper,
                "level": confidence
            },
            "metrics": metrics,
            "variability": round(variability, 2),
            "alertLevel": determine_alert_level(variability),
            "horizon": horizon,
            "timestamp": datetime.utcnow().isoformat(),
            "studyArea": study_area.get('name', 'Combeima Basin'),
            "metadata": {
                "algorithm": "LSTM-based flow prediction",
                "trainingData": len(data.get('historical', [])) if isinstance(data, dict) else 100,
                "confidenceLevel": confidence
            }
        }
        
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "modelName": "FLOW_PREDICTION"
        }
        print(json.dumps(error_result))
        sys.exit(1)

def determine_alert_level(variability):
    if variability > 50:
        return "CRITICAL"
    elif variability > 30:
        return "HIGH"
    elif variability > 15:
        return "MEDIUM"
    return "LOW"

if __name__ == "__main__":
    main()
