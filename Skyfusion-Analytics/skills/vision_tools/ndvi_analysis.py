#!/usr/bin/env python3
"""
NDVI Analysis Script for Skyfusion Analytics
Computes Normalized Difference Vegetation Index for the Combeima River Basin
"""

import json
import sys
import numpy as np
from datetime import datetime

def compute_ndvi(nir_band, red_band):
    """
    NDVI = (NIR - Red) / (NIR + Red)
    """
    np.seterr(divide='ignore', invalid='ignore')
    
    numerator = nir_band.astype(float) - red_band.astype(float)
    denominator = nir_band.astype(float) + red_band.astype(float)
    
    ndvi = np.divide(numerator, denominator)
    ndvi = np.nan_to_num(ndvi, nan=-1.0, posinf=1.0, neginf=-1.0)
    
    return ndvi

def main():
    try:
        input_data = json.loads(sys.stdin.read())
        
        data = input_data.get('data', {})
        study_area = input_data.get('studyArea', {})
        
        # Extract or generate band data
        nir_band = np.array(data.get('nir', [0.5, 0.6, 0.55, 0.65, 0.7]))
        red_band = np.array(data.get('red', [0.2, 0.25, 0.22, 0.28, 0.3]))
        
        # Compute NDVI
        ndvi_values = compute_ndvi(nir_band, red_band)
        
        # Calculate statistics
        valid_ndvi = ndvi_values[ndvi_values != -1.0]
        
        result = {
            "success": True,
            "analysisType": "NDVI",
            "ndvi": float(np.mean(valid_ndvi)) if len(valid_ndvi) > 0 else 0.0,
            "mean": float(np.mean(valid_ndvi)) if len(valid_ndvi) > 0 else 0.0,
            "stdDev": float(np.std(valid_ndvi)) if len(valid_ndvi) > 0 else 0.0,
            "min": float(np.min(valid_ndvi)) if len(valid_ndvi) > 0 else -1.0,
            "max": float(np.max(valid_ndvi)) if len(valid_ndvi) > 0 else 1.0,
            "coverage": float(len(valid_ndvi) / len(ndvi_values)) if len(ndvi_values) > 0 else 0.0,
            "resolution": "30m",
            "bands": ["NIR", "RED"],
            "algorithm": "NDVI = (NIR - RED) / (NIR + RED)",
            "timestamp": datetime.utcnow().isoformat(),
            "studyArea": study_area.get('name', 'Combeima Basin')
        }
        
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "analysisType": "NDVI"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
