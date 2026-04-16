#!/usr/bin/env python3
"""
NDWI Analysis Script for Skyfusion Analytics
Computes Normalized Difference Water Index for the Combeima River Basin
"""

import json
import sys
import numpy as np
from datetime import datetime

def compute_ndwi(green_band, nir_band):
    """
    NDWI = (Green - NIR) / (Green + NIR)
    Positive values indicate water bodies
    """
    np.seterr(divide='ignore', invalid='ignore')
    
    numerator = green_band.astype(float) - nir_band.astype(float)
    denominator = green_band.astype(float) + nir_band.astype(float)
    
    ndwi = np.divide(numerator, denominator)
    ndwi = np.nan_to_num(ndwi, nan=-1.0, posinf=1.0, neginf=-1.0)
    
    return ndwi

def main():
    try:
        input_data = json.loads(sys.stdin.read())
        
        data = input_data.get('data', {})
        study_area = input_data.get('studyArea', {})
        
        green_band = np.array(data.get('green', [0.3, 0.35, 0.32, 0.38, 0.4]))
        nir_band = np.array(data.get('nir', [0.5, 0.6, 0.55, 0.65, 0.7]))
        
        ndwi_values = compute_ndwi(green_band, nir_band)
        
        valid_ndwi = ndwi_values[ndwi_values != -1.0]
        
        water_bodies = valid_ndwi[valid_ndwi > 0.0]
        
        result = {
            "success": True,
            "analysisType": "NDWI",
            "ndwi": float(np.mean(valid_ndwi)) if len(valid_ndwi) > 0 else 0.0,
            "mean": float(np.mean(valid_ndwi)) if len(valid_ndwi) > 0 else 0.0,
            "stdDev": float(np.std(valid_ndwi)) if len(valid_ndvi) > 0 else 0.0,
            "min": float(np.min(valid_ndwi)) if len(valid_ndwi) > 0 else -1.0,
            "max": float(np.max(valid_ndwi)) if len(valid_ndwi) > 0 else 1.0,
            "waterCoverage": float(len(water_bodies) / len(ndwi_values)) if len(ndwi_values) > 0 else 0.0,
            "waterBodies": len(water_bodies),
            "resolution": "30m",
            "bands": ["GREEN", "NIR"],
            "algorithm": "NDWI = (GREEN - NIR) / (GREEN + NIR)",
            "timestamp": datetime.utcnow().isoformat(),
            "studyArea": study_area.get('name', 'Combeima Basin')
        }
        
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "analysisType": "NDWI"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
