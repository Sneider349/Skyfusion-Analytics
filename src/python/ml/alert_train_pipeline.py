"""
Pipeline de Entrenamiento - Clasificador de Alertas
Skyfusion Analytics

Pipeline completo para:
1. Generación de dataset sintético
2. Ajuste de hiperparámetros con GridSearchCV
3. Entrenamiento con mejores hiperparámetros
4. Evaluación y validación
5. Exportación para inferencia
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import (
    train_test_split,
    cross_val_score,
    StratifiedKFold
)
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    cohen_kappa_score,
    roc_auc_score
)
from sklearn.preprocessing import StandardScaler
import joblib

import sys
sys.path.append(str(Path(__file__).parent))

from alert_classifier import (
    AlertConfig,
    AlertDatasetGenerator,
    AlertRandomForestClassifier,
    AlertPredictor,
    ALERT_LABELS,
    create_sample_features
)


class AlertTrainingPipeline:
    """
    Pipeline completo de entrenamiento para el clasificador de alertas.
    """
    
    def __init__(
        self,
        output_dir: str = '../../data/output',
        model_dir: str = '../../data/models'
    ):
        self.output_dir = Path(output_dir)
        self.model_dir = Path(model_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = None
        self.dataset_generator = None
        self.classifier = None
        self.training_history = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
    
    def generate_dataset(
        self,
        n_samples: int = 5000,
        use_synthetic: bool = True,
        seed: int = 42
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Genera dataset para entrenamiento.
        
        Args:
            n_samples: Número de muestras
            use_synthetic: Si usar datos sintéticos
            seed: Semilla aleatoria
            
        Returns:
            Tupla de (X, y)
        """
        print('\n' + '='*60)
        print('FASE 1: GENERACIÓN DE DATASET')
        print('='*60)
        
        self.config = AlertConfig(n_samples=n_samples, random_state=seed)
        
        if use_synthetic:
            print(f'Generando {n_samples} muestras sintéticas...')
            self.dataset_generator = AlertDatasetGenerator(self.config)
            X, y = self.dataset_generator.generate_dataset()
            
            print(f'\nDataset generado:')
            print(f'  - Muestras: {len(X)}')
            print(f'  - Features: {X.shape[1]}')
            print(f'  - Features: {list(X.columns)}')
            
            print(f'\nDistribución de clases:')
            for i in range(4):
                count = np.sum(y == i)
                pct = count / len(y) * 100
                print(f'  - {ALERT_LABELS[i]} (nivel {i}): {count} ({pct:.1f}%)')
            
            return X, y
        
        else:
            raise NotImplementedError("Solo datos sintéticos disponibles actualmente")
    
    def prepare_data(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        test_size: float = 0.2,
        stratify: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
        """
        Prepara datos para entrenamiento.
        
        Args:
            X: Features
            y: Labels
            test_size: Proporción de test
            stratify: Si mantener proporciones de clase
            
        Returns:
            Tupla (X_train, X_test, y_train, y_test)
        """
        print('\n' + '='*60)
        print('FASE 2: PREPARACIÓN DE DATOS')
        print('='*60)
        
        stratify_param = y if stratify else None
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.config.random_state,
            stratify=stratify_param
        )
        
        print(f'Dataset dividido:')
        print(f'  - Entrenamiento: {len(X_train)} muestras ({100-test_size*100:.0f}%)')
        print(f'  - Prueba: {len(X_test)} muestras ({test_size*100:.0f}%)')
        
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        
        print(f'\nDistribución en entrenamiento:')
        for i in range(4):
            count = np.sum(y_train == i)
            print(f'  - {ALERT_LABELS[i]}: {count} ({count/len(y_train)*100:.1f}%)')
        
        print(f'\nDistribución en prueba:')
        for i in range(4):
            count = np.sum(y_test == i)
            print(f'  - {ALERT_LABELS[i]}: {count} ({count/len(y_test)*100:.1f}%)')
        
        return X_train, X_test, y_train, y_test
    
    def train_with_tuning(
        self,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        use_gridsearch: bool = True,
        n_jobs: int = -1
    ) -> AlertRandomForestClassifier:
        """
        Entrena el modelo con ajuste de hiperparámetros.
        
        Args:
            X_train: Features de entrenamiento
            y_train: Labels de entrenamiento
            use_gridsearch: Si usar GridSearchCV
            n_jobs: Núcleos paralelos
            
        Returns:
            Modelo entrenado
        """
        print('\n' + '='*60)
        print('FASE 3: ENTRENAMIENTO CON AJUSTE DE HIPERPARÁMETROS')
        print('='*60)
        
        self.classifier = AlertRandomForestClassifier(
            config=self.config,
            model_path=str(self.model_dir)
        )
        
        self.classifier.fit(X_train, y_train, use_gridsearch=use_gridsearch, n_jobs=n_jobs)
        
        return self.classifier
    
    def evaluate_model(
        self,
        X_test: pd.DataFrame,
        y_test: np.ndarray
    ) -> Dict:
        """
        Evalúa el modelo en datos de prueba.
        
        Args:
            X_test: Features de prueba
            y_test: Labels de prueba
            
        Returns:
            Diccionario con métricas
        """
        print('\n' + '='*60)
        print('FASE 4: EVALUACIÓN DEL MODELO')
        print('='*60)
        
        metrics = self.classifier.evaluate(X_test, y_test)
        
        print(f'\nMétricas principales:')
        print(f'  - Accuracy: {metrics["accuracy"]:.4f}')
        print(f'  - F1 (weighted): {metrics["f1_weighted"]:.4f}')
        print(f'  - F1 (macro): {metrics["f1_macro"]:.4f}')
        print(f'  - Precision (weighted): {metrics["precision_weighted"]:.4f}')
        print(f'  - Recall (weighted): {metrics["recall_weighted"]:.4f}')
        
        print(f'\nConfusion Matrix:')
        cm = metrics['confusion_matrix']
        print(f'               Predicha')
        print(f'            green  yellow  orange  red')
        for i, row in enumerate(cm):
            labels = ['green', 'yellow', 'orange', 'red']
            print(f'  {labels[i]:>6}  {row[0]:5}  {row[1]:5}  {row[2]:5}  {row[3]:5}')
        
        print(f'\nClassification Report:')
        print(metrics['classification_report'])
        
        importance = self.classifier.get_feature_importance()
        print(f'\nTop 5 Features más importantes:')
        for idx, row in importance.head(5).iterrows():
            print(f'  {row["feature"]}: {row["importance"]:.4f}')
        
        return metrics
    
    def save_model(
        self,
        name: str = 'alert_classifier',
        save_dataset: bool = True
    ):
        """
        Guarda el modelo y resultados.
        
        Args:
            name: Nombre del modelo
            save_dataset: Si guardar el dataset generado
        """
        print('\n' + '='*60)
        print('FASE 5: GUARDADO DEL MODELO')
        print('='*60)
        
        self.classifier.save_model(name)
        
        if save_dataset and self.dataset_generator is not None:
            dataset_path = self.output_dir / 'alert_dataset'
            dataset_path.mkdir(parents=True, exist_ok=True)
            
            X_full = pd.concat([self.X_train, self.X_test])
            y_full = np.concatenate([self.y_train, self.y_test])
            
            X_full.to_csv(dataset_path / 'features.csv', index=False)
            np.save(dataset_path / 'labels.npy', y_full)
            
            print(f'Dataset guardado en {dataset_path}')
        
        print(f'\nModelo guardado como: {name}')
    
    def run_full_pipeline(
        self,
        n_samples: int = 5000,
        test_size: float = 0.2,
        use_gridsearch: bool = True,
        n_jobs: int = -1,
        model_name: str = 'alert_classifier'
    ) -> Dict:
        """
        Ejecuta el pipeline completo de entrenamiento.
        
        Args:
            n_samples: Número de muestras
            test_size: Proporción de test
            use_gridsearch: Si usar GridSearchCV
            n_jobs: Núcleos paralelos
            model_name: Nombre del modelo
            
        Returns:
            Diccionario con resultados
        """
        print('\n' + '#'*60)
        print('# SKYFUSION ANALYTICS - PIPELINE DE ENTRENAMIENTO')
        print('# Clasificador de Alertas (Random Forest)')
        print('#'*60)
        
        start_time = datetime.now()
        
        X, y = self.generate_dataset(n_samples=n_samples)
        
        X_train, X_test, y_train, y_test = self.prepare_data(
            X, y, test_size=test_size
        )
        
        classifier = self.train_with_tuning(
            X_train, y_train,
            use_gridsearch=use_gridsearch,
            n_jobs=n_jobs
        )
        
        metrics = self.evaluate_model(X_test, y_test)
        
        self.save_model(model_name)
        
        training_time = datetime.now() - start_time
        
        print('\n' + '#'*60)
        print('# ENTRENAMIENTO COMPLETADO')
        print(f'# Tiempo total: {training_time}')
        print('#'*60)
        
        return {
            'config': {
                'n_samples': n_samples,
                'test_size': test_size,
                'cv_folds': self.config.cv_folds
            },
            'best_params': classifier.best_params,
            'metrics': metrics,
            'training_time': str(training_time)
        }
    
    def generate_report(self, results: Dict, output_path: str = None):
        """
        Genera reporte de entrenamiento en JSON.
        
        Args:
            results: Resultados del entrenamiento
            output_path: Ruta de salida
        """
        output_path = output_path or str(self.output_dir / 'training_report.json')
        
        report = {
            'pipeline': 'AlertClassifierPipeline',
            'generated_at': datetime.now().isoformat(),
            'results': results
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f'Reporte guardado en {output_path}')


def main():
    parser = argparse.ArgumentParser(
        description='Pipeline de entrenamiento - Clasificador de Alertas'
    )
    
    parser.add_argument(
        '--samples', type=int, default=5000,
        help='Número de muestras (default: 5000)'
    )
    parser.add_argument(
        '--test-size', type=float, default=0.2,
        help='Proporción de test (default: 0.2)'
    )
    parser.add_argument(
        '--cv-folds', type=int, default=5,
        help='Número de folds para CV (default: 5)'
    )
    parser.add_argument(
        '--no-gridsearch', action='store_true',
        help='Desactivar GridSearchCV (usar default params)'
    )
    parser.add_argument(
        '--jobs', type=int, default=-1,
        help='Núcleos paralelos (-1 = todos, default: -1)'
    )
    parser.add_argument(
        '--model-name', type=str, default='alert_classifier',
        help='Nombre del modelo (default: alert_classifier)'
    )
    parser.add_argument(
        '--quick-test', action='store_true',
        help='quick test con menos muestras y parámetros'
    )
    
    args = parser.parse_args()
    
    if args.quick_test:
        args.samples = 1000
        args.cv_folds = 3
        print('Quick test mode: muestras=1000, folds=3')
    
    pipeline = AlertTrainingPipeline()
    
    results = pipeline.run_full_pipeline(
        n_samples=args.samples,
        test_size=args.test_size,
        use_gridsearch=not args.no_gridsearch,
        n_jobs=args.jobs,
        model_name=args.model_name
    )
    
    pipeline.generate_report(results)
    
    print('\n' + '='*60)
    print('PIPELINE COMPLETADO EXITOSAMENTE')
    print('='*60)


if __name__ == '__main__':
    main()