"""
Clasificador de Alertas para Skyfusion Analytics
Random Forest con ajuste de hiperparámetros usando GridSearchCV + K-Fold Cross-Validation

Clasificación supervisada de 4 niveles de alerta:
- 0 (green): Condiciones normales
- 1 (yellow): Vigilancia
- 2 (orange): Alerta activa
- 3 (red): Emergencia
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    GridSearchCV, 
    KFold, 
    cross_val_score,
    train_test_split
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, 
    classification_report, 
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer


@dataclass
class AlertConfig:
    """Configuración del clasificador de alertas."""
    n_samples: int = 5000
    test_size: float = 0.2
    random_state: int = 42
    cv_folds: int = 5
    
    n_estimators: List[int] = None
    max_depth: List[Any] = None
    min_samples_split: List[int] = None
    min_samples_leaf: List[int] = None
    max_features: List[Any] = None
    
    def __post_init__(self):
        self.n_estimators = self.n_estimators or [50, 100, 200]
        self.max_depth = self.max_depth or [5, 10, 15, None]
        self.min_samples_split = self.min_samples_split or [2, 5, 10]
        self.min_samples_leaf = self.min_samples_leaf or [1, 2, 4]
        self.max_features = self.max_features or ['sqrt', 'log2', None]


ALERT_LABELS = {
    0: 'green',
    1: 'yellow', 
    2: 'orange',
    3: 'red'
}

ALERT_COLORS = {
    0: '#22C55E',
    1: '#EAB308',
    2: '#F97316',
    3: '#EF4444'
}

ALERT_MESSAGES = {
    0: 'Condiciones normales. Sistema hídrico operando dentro de parámetros esperados.',
    1: 'Vigilancia recomendada. Se observan desviaciones moderadas que requieren monitoreo.',
    2: 'Alerta activa. Condiciones adversas podrían escalar si continúan.',
    3: 'EMERGENCIA hídrica. Intervención inmediata requerida.'
}


class AlertDatasetGenerator:
    """
    Generador de dataset sintético para clasificación de alertas.
    Crea datos realista basados en la dinámica hidrlógica de la cuenca Combeima.
    """
    
    def __init__(self, config: AlertConfig = None):
        self.config = config or AlertConfig()
        self.feature_names = [
            'caudal', 'caudal_change_pct', 'precip_24h', 'precip_48h',
            'precip_7d', 'temperature', 'humidity', 'ndvi', 'ndvi_trend',
            'ndwi', 'month'
        ]
    
    def _generate_temporal_features(self, n_samples: int, seed: int) -> pd.DataFrame:
        """Genera características temporales base."""
        np.random.seed(seed)
        n_days = n_samples
        
        base_caudal = 4.5
        seasonal = 1.5 * np.sin(2 * np.pi * np.arange(n_days) / 365)
        trend = np.linspace(0, 0.5, n_days)
        noise = np.random.normal(0, 0.3, n_days)
        caudal = base_caudal + seasonal + trend + noise
        caudal = np.clip(caudal, 0.5, 15)
        
        precipitation = np.random.exponential(5, n_days)
        precipitation = np.clip(precipitation, 0, 80)
        
        precipitation_7d = np.convolve(precipitation, np.ones(7)/7, mode='same')
        
        precipitation_48h = np.array([
            precipitation[max(0, i-1)] + precipitation[i] 
            for i in range(n_days)
        ])
        
        temperature = 22 + 5 * np.sin(2 * np.pi * np.arange(n_days) / 365) + np.random.normal(0, 2, n_days)
        temperature = np.clip(temperature, 10, 35)
        
        humidity = 70 + 15 * np.sin(2 * np.pi * np.arange(n_days) / 365 + np.pi) + np.random.normal(0, 5, n_days)
        humidity = np.clip(humidity, 30, 100)
        
        ndvi = 0.5 + 0.2 * np.sin(2 * np.pi * np.arange(n_days) / 365) + np.random.normal(0, 0.08, n_days)
        ndvi = np.clip(ndvi, 0.1, 0.9)
        
        ndvi_trend = np.gradient(ndvi)
        ndvi_trend = np.clip(ndvi_trend, -0.1, 0.1)
        
        ndwi = 0.15 + 0.1 * np.sin(2 * np.pi * np.arange(n_days) / 365) + np.random.normal(0, 0.05, n_days)
        ndwi = np.clip(ndwi, -0.3, 0.5)
        
        month = pd.date_range(start='2020-01-01', periods=n_days, freq='D').month
        
        return pd.DataFrame({
            'caudal': caudal,
            'precip_24h': precipitation,
            'precip_48h': precipitation_48h,
            'precip_7d': precipitation_7d,
            'temperature': temperature,
            'humidity': humidity,
            'ndvi': ndvi,
            'ndvi_trend': ndvi_trend,
            'ndwi': ndwi,
            'month': month
        })
    
    def _calculate_caudal_change(self, df: pd.DataFrame) -> pd.Series:
        """Calcula cambio porcentual de caudal vs media histórica."""
        rolling_mean = df['caudal'].rolling(window=30, min_periods=1).mean()
        caudal_mean = df['caudal'].mean()
        change_pct = ((rolling_mean - caudal_mean) / caudal_mean) * 100
        return change_pct
    
    def _assign_alert_labels(self, df: pd.DataFrame) -> np.ndarray:
        """
        Asigna etiquetas de alerta basándose en reglas hidrlógicas.
        
        Lógica:
        - RED (3): Caudal muy bajo (<30% media) o muy alto (>200% media), o NDVI muy bajo
        - ORANGE (2): Caudal bajo (<50% media) o alto (>150% media)
        - YELLOW (1): Algun indicador fuera de rango normal
        - GREEN (0): Condiciones normales
        """
        np.random.seed(42)
        labels = np.zeros(len(df), dtype=int)
        
        caudal_mean = df['caudal'].mean()
        caudal_std = df['caudal'].std()
        
        for i in range(len(df)):
            caudal = df['caudal'].iloc[i]
            precip = df['precip_24h'].iloc[i]
            ndvi = df['ndvi'].iloc[i]
            precip_7d = df['precip_7d'].iloc[i]
            humidity = df['humidity'].iloc[i]
            
            caudal_ratio = caudal / caudal_mean
            
            score = 0
            
            if caudal_ratio < 0.3:
                score += 3
            elif caudal_ratio < 0.5:
                score += 2
            elif caudal_ratio < 0.7:
                score += 1
            elif caudal_ratio > 2.0:
                score += 3
            elif caudal_ratio > 1.5:
                score += 2
            elif caudal_ratio > 1.2:
                score += 1
            
            if precip_7d < 2:
                score += 2
            elif precip_7d < 5:
                score += 1
            
            if precip < 0.5 and precip_7d < 3:
                score += 1
            
            if ndvi < 0.2:
                score += 2
            elif ndvi < 0.3:
                score += 1
            
            if humidity < 40:
                score += 1
            
            if np.random.random() < 0.05:
                score += np.random.randint(2, 4)
            
            if score >= 5:
                labels[i] = 3
            elif score >= 3:
                labels[i] = 2
            elif score >= 1:
                labels[i] = 1
            else:
                labels[i] = 0
        
        label_0_count = np.sum(labels == 0)
        label_1_count = np.sum(labels == 1)
        label_2_count = np.sum(labels == 2)
        label_3_count = np.sum(labels == 3)
        
        if label_3_count == 0:
            critical_indices = np.argsort(df['caudal'].values)[:int(len(df) * 0.03)]
            labels[critical_indices] = 3
            label_3_count = len(critical_indices)
        
        if label_2_count == 0:
            low_precip_indices = np.argsort(df['precip_7d'].values)[:int(len(df) * 0.05)]
            low_precip_indices = [i for i in low_precip_indices if labels[i] != 3][:int(len(df) * 0.02)]
            labels[low_precip_indices] = 2
        
        return labels
    
    def generate_dataset(self, n_samples: int = None, seed: int = None) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Genera dataset completo con etiquetas.
        
        Args:
            n_samples: Número de muestras
            seed: Semilla aleatoria
            
        Returns:
            Tupla de (DataFrame features, Array labels)
        """
        n_samples = n_samples or self.config.n_samples
        seed = seed or self.config.random_state
        
        df = self._generate_temporal_features(n_samples, seed)
        df['caudal_change_pct'] = self._calculate_caudal_change(df)
        
        labels = self._assign_alert_labels(df)
        
        df = df[self.feature_names]
        
        return df, labels
    
    def get_feature_names(self) -> List[str]:
        """Retorna nombres de features."""
        return self.feature_names.copy()


class AlertRandomForestClassifier:
    """
    Clasificador Random Forest para alertas hídricas.
    Incluye GridSearchCV para ajuste de hiperparámetros.
    """
    
    def __init__(
        self,
        config: AlertConfig = None,
        model_path: str = "../../data/models"
    ):
        self.config = config or AlertConfig()
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.best_params = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.label_encoder = LabelEncoder()
        self.cv_results = None
        
        self._param_grid = {
            'classifier__n_estimators': self.config.n_estimators,
            'classifier__max_depth': self.config.max_depth,
            'classifier__min_samples_split': self.config.min_samples_split,
            'classifier__min_samples_leaf': self.config.min_samples_leaf,
            'classifier__max_features': self.config.max_features
        }
    
    def _create_base_pipeline(self) -> Pipeline:
        """Crea pipeline base con scaler y classifier."""
        return Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                random_state=self.config.random_state,
                n_jobs=-1,
                class_weight='balanced'
            ))
        ])
    
    def _create_param_grid(self) -> Dict:
        """Crea grid de hiperparámetros."""
        return {
            'classifier__n_estimators': self.config.n_estimators,
            'classifier__max_depth': self.config.max_depth,
            'classifier__min_samples_split': self.config.min_samples_split,
            'classifier__min_samples_leaf': self.config.min_samples_leaf,
            'classifier__max_features': self.config.max_features
        }
    
    def fit(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        use_gridsearch: bool = True,
        n_jobs: int = -1
    ) -> 'AlertRandomForestClassifier':
        """
        Entrena el clasificador.
        
        Args:
            X: Features de entrenamiento
            y: Labels de entrenamiento
            use_gridsearch: Si usar GridSearchCV para hyperparameter tuning
            n_jobs: Núcleos para paralelización (-1 = todos)
            
        Returns:
            Self para chaining
        """
        self.feature_names = list(X.columns)
        
        X_scaled = self.scaler.fit_transform(X)
        
        pipeline = self._create_base_pipeline()
        
        kfold = KFold(
            n_splits=self.config.cv_folds,
            shuffle=True,
            random_state=self.config.random_state
        )
        
        if use_gridsearch:
            print('\n' + '='*60)
            print('AJUSTE DE HIPERPARÁMETROS (GridSearchCV)')
            print('='*60)
            
            param_grid = self._create_param_grid()
            
            total_combinations = (
                len(param_grid['classifier__n_estimators']) *
                len(param_grid['classifier__max_depth']) *
                len(param_grid['classifier__min_samples_split']) *
                len(param_grid['classifier__min_samples_leaf']) *
                len(param_grid['classifier__max_features'])
            )
            print(f'Combinaciones a evaluar: {total_combinations}')
            print(f'K-Fold: {self.config.cv_folds}')
            print(f'Total fits: {total_combinations * self.config.cv_folds}')
            
            grid_search = GridSearchCV(
                pipeline,
                param_grid,
                cv=kfold,
                scoring='accuracy',
                n_jobs=n_jobs,
                verbose=1,
                return_train_score=True
            )
            
            grid_search.fit(X_scaled, y)
            
            self.model = grid_search.best_estimator_
            self.best_params = grid_search.best_params_
            self.cv_results = grid_search.cv_results_
            
            print(f'\nMejores hiperparámetros:')
            for param, value in self.best_params.items():
                print(f'  {param}: {value}')
            print(f'Best CV Score (Accuracy): {grid_search.best_score_:.4f}')
            
        else:
            pipeline.fit(X_scaled, y)
            self.model = pipeline
            
            scores = cross_val_score(pipeline, X_scaled, y, cv=kfold, scoring='accuracy')
            print(f'\nCross-Validation Accuracy: {scores.mean():.4f} (+/- {scores.std()*2:.4f})')
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predice etiquetas de alerta.
        
        Args:
            X: Features
            
        Returns:
            Array de predicciones (0-3)
        """
        if self.model is None:
            raise ValueError('Modelo no entrenado. Llama fit() primero.')
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predice probabilidades de cada clase.
        
        Args:
            X: Features
            
        Returns:
            Array de probabilidades [n_samples, n_classes]
        """
        if self.model is None:
            raise ValueError('Modelo no entrenado. Llama fit() primero.')
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def evaluate(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        return_report: bool = True
    ) -> Dict[str, float]:
        """
        Evalúa el modelo.
        
        Args:
            X: Features de test
            y: Labels de test
            return_report: Si incluir classification report
            
        Returns:
            Diccionario con métricas
        """
        if self.model is None:
            raise ValueError('Modelo no entrenado.')
        
        X_scaled = self.scaler.transform(X)
        y_pred = self.model.predict(X_scaled)
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'f1_weighted': f1_score(y, y_pred, average='weighted'),
            'f1_macro': f1_score(y, y_pred, average='macro'),
            'precision_weighted': precision_score(y, y_pred, average='weighted', zero_division=0),
            'recall_weighted': recall_score(y, y_pred, average='weighted')
        }
        
        unique_labels = sorted(np.unique(np.concatenate([y, y_pred])))
        target_names = [ALERT_LABELS[l] for l in unique_labels]
        
        if return_report:
            metrics['classification_report'] = classification_report(
                y, y_pred, 
                labels=unique_labels,
                target_names=target_names,
                zero_division=0
            )
            metrics['confusion_matrix'] = confusion_matrix(y, y_pred, labels=unique_labels).tolist()
        
        return metrics
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Obtiene importancia de features.
        
        Returns:
            DataFrame con feature_names e importances
        """
        if self.model is None:
            raise ValueError('Modelo no entrenado.')
        
        importances = self.model.named_steps['classifier'].feature_importances_
        
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
    
    def save_model(self, name: str = 'alert_classifier'):
        """
        Guarda el modelo y configuración.
        
        Args:
            name: Nombre del modelo
        """
        import joblib
        
        model_file = self.model_path / f'{name}.joblib'
        config_file = self.model_path / f'{name}_config.json'
        scaler_file = self.model_path / f'{name}_scaler.joblib'
        
        joblib.dump(self.model, model_file)
        joblib.dump(self.scaler, scaler_file)
        
        config = {
            'feature_names': self.feature_names,
            'best_params': self.best_params,
            'cv_folds': self.config.cv_folds,
            'cv_results': self.cv_results,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f'Modelo guardado en {model_file}')
        print(f'Configuración guardada en {config_file}')
    
    def load_model(self, name: str = 'alert_classifier'):
        """
        Carga un modelo guardado.
        
        Args:
            name: Nombre del modelo
        """
        import joblib
        
        model_file = self.model_path / f'{name}.joblib'
        config_file = self.model_path / f'{name}_config.json'
        scaler_file = self.model_path / f'{name}_scaler.joblib'
        
        self.model = joblib.load(model_file)
        self.scaler = joblib.load(scaler_file)
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.feature_names = config['feature_names']
        self.best_params = config['best_params']
        
        print(f'Modelo cargado desde {model_file}')


class AlertPredictor:
    """
    Interfaz simplificada para predicción de alertas.
    """
    
    def __init__(self, model_path: str = "../../data/models"):
        self.classifier = None
        self.model_path = Path(model_path)
        
    def load(self, name: str = 'alert_classifier'):
        """Carga el modelo."""
        self.classifier = AlertRandomForestClassifier(model_path=str(self.model_path))
        self.classifier.load_model(name)
        
    def predict(self, features: Dict) -> Dict:
        """
        Predice alerta para una muestra.
        
        Args:
            features: Diccionario con features requeridas
            
        Returns:
            Diccionario con predicción y metadatos
        """
        if self.classifier is None:
            raise ValueError('Modelo no cargado. Llama load() primero.')
        
        feature_names = self.classifier.feature_names
        
        X = pd.DataFrame([features])[feature_names]
        
        alert_level = self.classifier.predict(X)[0]
        probabilities = self.classifier.predict_proba(X)[0]
        
        return {
            'alert_level': int(alert_level),
            'alert_name': ALERT_LABELS[alert_level],
            'alert_color': ALERT_COLORS[alert_level],
            'alert_message': ALERT_MESSAGES[alert_level],
            'probabilities': {
                ALERT_LABELS[i]: float(probabilities[i]) 
                for i in range(4)
            }
        }
    
    def predict_batch(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Predice alertas para múltiples muestras.
        
        Args:
            features_df: DataFrame con features
            
        Returns:
            DataFrame con predicciones
        """
        if self.classifier is None:
            raise ValueError('Modelo no cargado. Llama load() primero.')
        
        feature_names = self.classifier.feature_names
        X = features_df[feature_names]
        
        predictions = self.classifier.predict(X)
        probabilities = self.classifier.predict_proba(X)
        
        results = pd.DataFrame({
            'alert_level': predictions,
            'alert_name': [ALERT_LABELS[p] for p in predictions],
            'alert_color': [ALERT_COLORS[p] for p in predictions]
        })
        
        prob_cols = [f'prob_{ALERT_LABELS[i]}' for i in range(4)]
        for i, col in enumerate(prob_cols):
            results[col] = probabilities[:, i]
        
        return results


def create_sample_features(
    caudal: float = 4.5,
    precip_24h: float = 5.0,
    precip_48h: float = 10.0,
    precip_7d: float = 25.0,
    temperature: float = 22.0,
    humidity: float = 70.0,
    ndvi: float = 0.5,
    ndvi_trend: float = 0.0,
    ndwi: float = 0.15,
    month: int = 6
) -> Dict:
    """
    Crea diccionario de features para predicción.
    Útil para testing manual.
    """
    caudal_mean = 4.5
    caudal_change = ((caudal - caudal_mean) / caudal_mean) * 100
    
    return {
        'caudal': caudal,
        'caudal_change_pct': caudal_change,
        'precip_24h': precip_24h,
        'precip_48h': precip_48h,
        'precip_7d': precip_7d,
        'temperature': temperature,
        'humidity': humidity,
        'ndvi': ndvi,
        'ndvi_trend': ndvi_trend,
        'ndwi': ndwi,
        'month': month
    }


if __name__ == '__main__':
    print('='*60)
    print('SKYFUSION ANALYTICS - CLASIFICADOR DE ALERTAS')
    print('Random Forest con GridSearchCV')
    print('='*60)
    
    config = AlertConfig(n_samples=3000)
    
    print('\n[1] Generando dataset sintético...')
    generator = AlertDatasetGenerator(config)
    X, y = generator.generate_dataset()
    
    print(f'    Features: {X.shape}')
    print(f'    Labels distribution:')
    for i in range(4):
        count = np.sum(y == i)
        print(f'      {ALERT_LABELS[i]}: {count} ({count/len(y)*100:.1f}%)')
    
    print('\n[2] Dividiendo dataset...')
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, 
        random_state=config.random_state, stratify=y
    )
    print(f'    Train: {len(X_train)}, Test: {len(X_test)}')
    
    print('\n[3] Entrenando modelo con GridSearchCV...')
    classifier = AlertRandomForestClassifier(config)
    classifier.fit(X_train, y_train, use_gridsearch=True)
    
    print('\n[4] Evaluando en test set...')
    metrics = classifier.evaluate(X_test, y_test)
    print(f'    Accuracy: {metrics["accuracy"]:.4f}')
    print(f'    F1 (weighted): {metrics["f1_weighted"]:.4f}')
    print(f'\nClassification Report:')
    print(metrics['classification_report'])
    
    print('\n[5] Feature Importance:')
    importance = classifier.get_feature_importance()
    for _, row in importance.head(5).iterrows():
        print(f'    {row["feature"]}: {row["importance"]:.4f}')
    
    print('\n[6] Guardando modelo...')
    classifier.save_model('alert_classifier')
    
    print('\n[7] Testing predicción...')
    predictor = AlertPredictor()
    predictor.load('alert_classifier')
    
    test_cases = [
        create_sample_features(caudal=4.5, precip_7d=30, ndvi=0.6),
        create_sample_features(caudal=1.5, precip_7d=2, ndvi=0.25),
        create_sample_features(caudal=8.0, precip_7d=50, ndvi=0.7),
        create_sample_features(caudal=0.8, precip_7d=1, ndvi=0.15),
    ]
    
    for i, features in enumerate(test_cases):
        result = predictor.predict(features)
        print(f'\n  Caso {i+1}:')
        print(f'    Alerta: {result["alert_name"]} ({result["alert_level"]})')
        print(f'    Color: {result["alert_color"]}')
        print(f'    Mensaje: {result["alert_message"]}')
        print(f'    Probs: {result["probabilities"]}')
    
    print('\n' + '='*60)
    print('CLASIFICADOR DE ALERTAS COMPLETADO')
    print('='*60)