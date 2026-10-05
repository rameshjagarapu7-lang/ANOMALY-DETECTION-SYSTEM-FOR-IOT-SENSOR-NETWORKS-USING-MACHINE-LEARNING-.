"""
Anomaly Detection System for IoT Sensor Networks
Implements real-time anomaly detection using machine learning
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.svm import OneClassSVM
from sklearn.covariance import EllipticEnvelope
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class IoTAnomalyDetectionSystem:
    def __init__(self):
        self.sensor_data = None
        self.anomalies = None
        self.models = {}
        self.scaler = StandardScaler()
        
    def generate_sensor_data(self, n_samples=5000, n_sensors=10):
        """Generate synthetic IoT sensor data with anomalies"""
        np.random.seed(42)
        
        # Generate timestamps
        start_date = datetime.now() - timedelta(days=30)
        timestamps = [start_date + timedelta(minutes=i) for i in range(n_samples)]
        
        # Generate normal sensor data
        data = {}
        data['timestamp'] = timestamps
        data['sensor_id'] = np.random.choice([f'SENSOR_{i:03d}' for i in range(n_sensors)], n_samples)
        
        # Temperature (normal: 20-30°C)
        data['temperature'] = np.random.normal(25, 2, n_samples)
        
        # Humidity (normal: 40-60%)
        data['humidity'] = np.random.normal(50, 5, n_samples)
        
        # Pressure (normal: 1000-1020 hPa)
        data['pressure'] = np.random.normal(1010, 5, n_samples)
        
        # Vibration (normal: 0-10 mm/s)
        data['vibration'] = np.random.exponential(2, n_samples)
        
        # Energy consumption (normal: 100-500 kWh)
        data['energy_consumption'] = np.random.normal(300, 50, n_samples)
        
        # Create anomaly labels
        data['is_anomaly'] = np.zeros(n_samples, dtype=int)
        
        # Introduce anomalies (5% of data)
        n_anomalies = int(0.05 * n_samples)
        anomaly_indices = np.random.choice(n_samples, n_anomalies, replace=False)
        
        for idx in anomaly_indices:
            anomaly_type = np.random.choice(['temperature', 'humidity', 'pressure', 'vibration', 'energy'])
            
            if anomaly_type == 'temperature':
                data['temperature'][idx] = np.random.choice([5, 45])  # Extreme temperature
            elif anomaly_type == 'humidity':
                data['humidity'][idx] = np.random.choice([10, 90])  # Extreme humidity
            elif anomaly_type == 'pressure':
                data['pressure'][idx] = np.random.choice([950, 1050])  # Extreme pressure
            elif anomaly_type == 'vibration':
                data['vibration'][idx] = np.random.uniform(20, 50)  # High vibration
            elif anomaly_type == 'energy':
                data['energy_consumption'][idx] = np.random.uniform(800, 1200)  # High consumption
            
            data['is_anomaly'][idx] = 1
        
        self.sensor_data = pd.DataFrame(data)
        self.sensor_data.to_csv('/home/ubuntu/iot_sensor_data.csv', index=False)
        print(f"Generated sensor data: {n_samples} samples from {n_sensors} sensors")
        print(f"Anomalies injected: {n_anomalies} ({n_anomalies/n_samples*100:.1f}%)")
        return self.sensor_data
    
    def preprocess_data(self):
        """Preprocess sensor data"""
        # Extract features
        feature_cols = ['temperature', 'humidity', 'pressure', 'vibration', 'energy_consumption']
        X = self.sensor_data[feature_cols].values
        y = self.sensor_data['is_anomaly'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y, feature_cols
    
    def train_anomaly_models(self):
        """Train multiple anomaly detection models"""
        X_scaled, y, _ = self.preprocess_data()
        
        # Split data (80-20)
        split_idx = int(0.8 * len(X_scaled))
        X_train = X_scaled[:split_idx]
        X_test = X_scaled[split_idx:]
        y_test = y[split_idx:]
        
        # Train models
        print("\nTraining anomaly detection models...")
        
        # 1. Isolation Forest
        print("[1] Training Isolation Forest...")
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        iso_forest.fit(X_train)
        y_pred_iso = iso_forest.predict(X_test)
        y_pred_iso = np.where(y_pred_iso == -1, 1, 0)  # Convert to binary
        
        # 2. One-Class SVM
        print("[2] Training One-Class SVM...")
        oc_svm = OneClassSVM(nu=0.05, kernel='rbf')
        oc_svm.fit(X_train)
        y_pred_svm = oc_svm.predict(X_test)
        y_pred_svm = np.where(y_pred_svm == -1, 1, 0)  # Convert to binary
        
        # 3. Elliptic Envelope
        print("[3] Training Elliptic Envelope...")
        ee = EllipticEnvelope(contamination=0.05, random_state=42)
        ee.fit(X_train)
        y_pred_ee = ee.predict(X_test)
        y_pred_ee = np.where(y_pred_ee == -1, 1, 0)  # Convert to binary
        
        # Evaluate models
        results = []
        
        for model_name, y_pred in [('Isolation Forest', y_pred_iso), 
                                    ('One-Class SVM', y_pred_svm), 
                                    ('Elliptic Envelope', y_pred_ee)]:
            results.append({
                'Model': model_name,
                'Accuracy': round(accuracy_score(y_test, y_pred), 4),
                'Precision': round(precision_score(y_test, y_pred, zero_division=0), 4),
                'Recall': round(recall_score(y_test, y_pred, zero_division=0), 4),
                'F1_Score': round(f1_score(y_test, y_pred, zero_division=0), 4)
            })
        
        results_df = pd.DataFrame(results)
        results_df.to_csv('/home/ubuntu/anomaly_model_results.csv', index=False)
        
        self.models = {
            'Isolation Forest': (iso_forest, y_pred_iso),
            'One-Class SVM': (oc_svm, y_pred_svm),
            'Elliptic Envelope': (ee, y_pred_ee)
        }
        
        print("Model training complete")
        return results_df
    
    def detect_anomalies(self):
        """Detect anomalies using ensemble approach"""
        X_scaled, y, _ = self.preprocess_data()
        
        # Use Isolation Forest for final predictions
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        iso_forest.fit(X_scaled)
        predictions = iso_forest.predict(X_scaled)
        anomaly_scores = iso_forest.score_samples(X_scaled)
        
        # Add predictions to dataframe
        self.sensor_data['anomaly_score'] = anomaly_scores
        self.sensor_data['predicted_anomaly'] = np.where(predictions == -1, 1, 0)
        self.sensor_data['detection_status'] = self.sensor_data['predicted_anomaly'].apply(
            lambda x: 'ANOMALY' if x == 1 else 'NORMAL'
        )
        
        self.sensor_data.to_csv('/home/ubuntu/iot_sensor_data_with_predictions.csv', index=False)
        print(f"Anomalies detected: {self.sensor_data['predicted_anomaly'].sum()} out of {len(self.sensor_data)}")
        
        return self.sensor_data
    
    def generate_visualizations(self):
        """Generate comprehensive anomaly detection visualizations"""
        X_scaled, y, feature_cols = self.preprocess_data()
        
        # 1. Sensor Data Distribution
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        for idx, col in enumerate(feature_cols):
            ax = axes[idx // 3, idx % 3]
            
            normal_data = self.sensor_data[self.sensor_data['is_anomaly'] == 0][col]
            anomaly_data = self.sensor_data[self.sensor_data['is_anomaly'] == 1][col]
            
            ax.hist(normal_data, bins=30, alpha=0.7, label='Normal', color='#3498db', edgecolor='black')
            ax.hist(anomaly_data, bins=30, alpha=0.7, label='Anomaly', color='#e74c3c', edgecolor='black')
            ax.set_xlabel(col, fontsize=10, fontweight='bold')
            ax.set_ylabel('Frequency', fontsize=10, fontweight='bold')
            ax.set_title(f'{col} Distribution', fontsize=11, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
        
        # Remove extra subplot
        fig.delaxes(axes[1, 2])
        
        plt.tight_layout()
        plt.savefig('/home/ubuntu/sensor_data_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved: sensor_data_distribution.png")
        
        # 2. Anomaly Detection Performance
        results_df = pd.read_csv('/home/ubuntu/anomaly_model_results.csv')
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        x = np.arange(len(results_df))
        width = 0.2
        
        axes[0].bar(x - width, results_df['Accuracy'], width, label='Accuracy', color='#3498db', edgecolor='black', linewidth=1.5)
        axes[0].bar(x, results_df['Precision'], width, label='Precision', color='#2ecc71', edgecolor='black', linewidth=1.5)
        axes[0].bar(x + width, results_df['Recall'], width, label='Recall', color='#e74c3c', edgecolor='black', linewidth=1.5)
        
        axes[0].set_ylabel('Score', fontsize=11, fontweight='bold')
        axes[0].set_title('Anomaly Detection Model Performance', fontsize=12, fontweight='bold')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(results_df['Model'], rotation=15, ha='right')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # F1-Score comparison
        axes[1].bar(results_df['Model'], results_df['F1_Score'], color='#f39c12', edgecolor='black', linewidth=1.5)
        axes[1].set_ylabel('F1-Score', fontsize=11, fontweight='bold')
        axes[1].set_title('F1-Score Comparison', fontsize=12, fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='y')
        plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=15, ha='right')
        
        plt.tight_layout()
        plt.savefig('/home/ubuntu/anomaly_model_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved: anomaly_model_performance.png")
        
        # 3. Anomaly Timeline
        fig, ax = plt.subplots(figsize=(14, 6))
        
        normal_data = self.sensor_data[self.sensor_data['predicted_anomaly'] == 0]
        anomaly_data = self.sensor_data[self.sensor_data['predicted_anomaly'] == 1]
        
        ax.scatter(normal_data.index, normal_data['temperature'], alpha=0.5, s=20, label='Normal', color='#3498db', edgecolors='black', linewidth=0.5)
        ax.scatter(anomaly_data.index, anomaly_data['temperature'], alpha=0.8, s=50, label='Anomaly', color='#e74c3c', marker='X', edgecolors='black', linewidth=1)
        
        ax.set_xlabel('Sample Index', fontsize=11, fontweight='bold')
        ax.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold')
        ax.set_title('Anomaly Detection Timeline - Temperature Sensor', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/home/ubuntu/anomaly_timeline.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved: anomaly_timeline.png")
        
        # 4. Sensor Health Status
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Anomaly rate by sensor
        anomaly_by_sensor = self.sensor_data.groupby('sensor_id')['predicted_anomaly'].agg(['sum', 'count'])
        anomaly_by_sensor['rate'] = (anomaly_by_sensor['sum'] / anomaly_by_sensor['count'] * 100).round(2)
        
        axes[0, 0].bar(range(len(anomaly_by_sensor)), anomaly_by_sensor['rate'], color='#e74c3c', edgecolor='black', linewidth=1.5)
        axes[0, 0].set_ylabel('Anomaly Rate (%)', fontsize=11, fontweight='bold')
        axes[0, 0].set_title('Anomaly Rate by Sensor', fontsize=12, fontweight='bold')
        axes[0, 0].set_xticks(range(len(anomaly_by_sensor)))
        axes[0, 0].set_xticklabels(anomaly_by_sensor.index, rotation=45, ha='right')
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        # Anomaly count distribution
        anomaly_counts = self.sensor_data['predicted_anomaly'].value_counts()
        axes[0, 1].pie([anomaly_counts.get(0, 0), anomaly_counts.get(1, 0)], 
                       labels=['Normal', 'Anomaly'], 
                       autopct='%1.1f%%',
                       colors=['#3498db', '#e74c3c'],
                       startangle=90,
                       explode=(0, 0.1))
        axes[0, 1].set_title('Overall Anomaly Distribution', fontsize=12, fontweight='bold')
        
        # Temperature anomalies
        temp_anomalies = self.sensor_data[self.sensor_data['predicted_anomaly'] == 1]['temperature']
        axes[1, 0].hist(temp_anomalies, bins=20, color='#e74c3c', edgecolor='black', linewidth=1.5)
        axes[1, 0].set_xlabel('Temperature (°C)', fontsize=11, fontweight='bold')
        axes[1, 0].set_ylabel('Frequency', fontsize=11, fontweight='bold')
        axes[1, 0].set_title('Temperature Anomalies Distribution', fontsize=12, fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Anomaly score distribution
        axes[1, 1].hist(self.sensor_data['anomaly_score'], bins=30, color='#9b59b6', edgecolor='black', linewidth=1.5)
        axes[1, 1].set_xlabel('Anomaly Score', fontsize=11, fontweight='bold')
        axes[1, 1].set_ylabel('Frequency', fontsize=11, fontweight='bold')
        axes[1, 1].set_title('Anomaly Score Distribution', fontsize=12, fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('/home/ubuntu/sensor_health_status.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved: sensor_health_status.png")
        
        # 5. Confusion Matrices
        X_scaled, y, _ = self.preprocess_data()
        split_idx = int(0.8 * len(X_scaled))
        X_test = X_scaled[split_idx:]
        y_test = y[split_idx:]
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        model_names = ['Isolation Forest', 'One-Class SVM', 'Elliptic Envelope']
        
        for idx, (model_name, (model, y_pred)) in enumerate(self.models.items()):
            cm = confusion_matrix(y_test, y_pred)
            
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx], 
                       cbar=False, xticklabels=['Normal', 'Anomaly'], 
                       yticklabels=['Normal', 'Anomaly'])
            axes[idx].set_title(f'{model_name} Confusion Matrix', fontsize=11, fontweight='bold')
            axes[idx].set_ylabel('True Label', fontsize=10, fontweight='bold')
            axes[idx].set_xlabel('Predicted Label', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('/home/ubuntu/confusion_matrices.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("Saved: confusion_matrices.png")

def main():
    print("="*80)
    print("ANOMALY DETECTION SYSTEM FOR IOT SENSOR NETWORKS")
    print("="*80)
    
    print("\n[1] Initializing IoT anomaly detection system...")
    system = IoTAnomalyDetectionSystem()
    
    print("\n[2] Generating sensor data...")
    system.generate_sensor_data(n_samples=5000, n_sensors=10)
    
    print("\n[3] Training anomaly detection models...")
    system.train_anomaly_models()
    
    print("\n[4] Detecting anomalies...")
    system.detect_anomalies()
    
    print("\n[5] Generating visualizations...")
    system.generate_visualizations()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE - All files generated successfully")
    print("="*80)

if __name__ == "__main__":
    main()
