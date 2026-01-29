"""
AI-Powered Churn Prediction System
Predicts which members are likely to cancel using machine learning
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
import os


class ChurnPredictor:
    """Machine learning model to predict member churn"""
    
    def __init__(self, model_path='models/churn_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.feature_names = None
        
        # Load existing model if available
        if os.path.exists(model_path):
            self.load_model()
    
    def extract_features(self, member_data: Dict) -> Dict:
        """
        Extract predictive features from member data
        
        Args:
            member_data: Dict with member info, fees, attendance
        
        Returns:
            Dict of engineered features
        """
        today = datetime.now().date()
        
        # Basic info
        join_date = datetime.strptime(member_data['joined_date'], '%Y-%m-%d').date()
        tenure_days = (today - join_date).days
        
        # Attendance features
        attendance = member_data.get('attendance', [])
        recent_30_days = [a for a in attendance if (today - datetime.strptime(a['date'], '%Y-%m-%d').date()).days <= 30]
        recent_60_days = [a for a in attendance if (today - datetime.strptime(a['date'], '%Y-%m-%d').date()).days <= 60]
        
        attendance_last_30 = len(recent_30_days)
        attendance_last_60 = len(recent_60_days)
        attendance_frequency = attendance_last_30 / 4.3 if attendance_last_30 > 0 else 0  # visits per week
        
        # Attendance decline
        if len(recent_60_days) > 0:
            first_30 = len([a for a in recent_60_days if (today - datetime.strptime(a['date'], '%Y-%m-%d').date()).days > 30])
            second_30 = attendance_last_30
            attendance_decline = ((first_30 - second_30) / first_30 * 100) if first_30 > 0 else 0
        else:
            attendance_decline = 0
        
        # Days since last visit
        if attendance:
            last_visit = max([datetime.strptime(a['date'], '%Y-%m-%d').date() for a in attendance])
            days_since_visit = (today - last_visit).days
        else:
            days_since_visit = tenure_days
        
        # Payment features
        fees = member_data.get('fees', [])
        total_payments = len(fees)
        
        # Late payment rate
        late_payments = sum(1 for f in fees if self._is_late_payment(f))
        late_payment_rate = (late_payments / total_payments * 100) if total_payments > 0 else 0
        
        # Payment gaps (missed months)
        payment_gaps = self._calculate_payment_gaps(fees, tenure_days)
        
        # Engagement score (composite)
        engagement_score = self._calculate_engagement_score(
            attendance_frequency,
            days_since_visit,
            late_payment_rate
        )
        
        # Demographics
        age = self._calculate_age(member_data.get('birthday'))
        
        return {
            'tenure_months': tenure_days / 30,
            'attendance_frequency': attendance_frequency,
            'attendance_last_30': attendance_last_30,
            'attendance_decline': attendance_decline,
            'days_since_visit': days_since_visit,
            'total_payments': total_payments,
            'late_payment_rate': late_payment_rate,
            'payment_gaps': payment_gaps,
            'engagement_score': engagement_score,
            'age': age if age else 30,  # default to 30 if unknown
            'is_trial': int(member_data.get('is_trial', False))
        }
    
    def _is_late_payment(self, fee: Dict) -> bool:
        """Check if payment was late (paid after month end)"""
        try:
            month_str = fee['month']  # e.g., "2024-01"
            paid_date = datetime.strptime(fee['paid_date'], '%Y-%m-%d')
            month_end = datetime.strptime(f"{month_str}-28", '%Y-%m-%d')  # Conservative estimate
            return paid_date > month_end
        except:
            return False
    
    def _calculate_payment_gaps(self, fees: List[Dict], tenure_days: int) -> int:
        """Calculate number of missed payment months"""
        if not fees or tenure_days < 30:
            return 0
        
        expected_payments = tenure_days // 30
        actual_payments = len(fees)
        return max(0, expected_payments - actual_payments)
    
    def _calculate_engagement_score(self, attendance_freq: float, days_since: int, late_rate: float) -> float:
        """
        Calculate engagement score (0-100)
        Higher = more engaged
        """
        # Attendance component (0-50 points)
        attendance_points = min(50, attendance_freq * 12.5)  # 4 visits/week = 50 points
        
        # Recency component (0-30 points)
        if days_since <= 7:
            recency_points = 30
        elif days_since <= 14:
            recency_points = 20
        elif days_since <= 30:
            recency_points = 10
        else:
            recency_points = 0
        
        # Reliability component (0-20 points)
        reliability_points = max(0, 20 - (late_rate / 5))
        
        return attendance_points + recency_points + reliability_points
    
    def _calculate_age(self, birthday: str) -> int:
        """Calculate age from birthday"""
        if not birthday:
            return None
        try:
            birth_date = datetime.strptime(birthday, '%Y-%m-%d')
            today = datetime.now()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except:
            return None
    
    def train_model(self, training_data: List[Dict]):
        """
        Train the churn prediction model
        
        Args:
            training_data: List of dicts with member data and 'churned' label
        """
        # Extract features for all members
        features_list = []
        labels = []
        
        for member in training_data:
            features = self.extract_features(member)
            features_list.append(features)
            labels.append(int(member.get('churned', False)))
        
        # Convert to DataFrame
        df = pd.DataFrame(features_list)
        self.feature_names = df.columns.tolist()
        
        X = df.values
        y = np.array(labels)
        
        # Split for validation
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        
        print(f"Model Training Complete:")
        print(f"  Accuracy: {accuracy:.2%}")
        print(f"  Precision: {precision:.2%}")
        print(f"  Recall: {recall:.2%}")
        
        # Feature importance
        importances = self.model.feature_importances_
        feature_importance = sorted(zip(self.feature_names, importances), key=lambda x: x[1], reverse=True)
        print("\nTop Features:")
        for name, importance in feature_importance[:5]:
            print(f"  {name}: {importance:.3f}")
        
        # Save model
        self.save_model()
        
        return accuracy
    
    def predict_churn(self, member_data: Dict) -> Tuple[float, Dict]:
        """
        Predict churn probability for a member
        
        Returns:
            (churn_probability, risk_factors)
        """
        if not self.model:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        # Extract features
        features = self.extract_features(member_data)
        
        # Convert to array in correct order
        X = pd.DataFrame([features])[self.feature_names].values
        
        # Predict probability
        churn_prob = self.model.predict_proba(X)[0][1]  # Probability of class 1 (churned)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(features)
        
        return churn_prob, risk_factors
    
    def _identify_risk_factors(self, features: Dict) -> Dict:
        """Identify key risk factors for a member"""
        risks = {}
        
        # Attendance risks
        if features['attendance_frequency'] < 1:
            risks['low_attendance'] = 'Visits less than once per week'
        
        if features['attendance_decline'] > 30:
            risks['attendance_drop'] = f"Attendance declined {features['attendance_decline']:.0f}%"
        
        if features['days_since_visit'] > 14:
            risks['inactive'] = f"No visit in {features['days_since_visit']} days"
        
        # Payment risks
        if features['late_payment_rate'] > 20:
            risks['payment_issues'] = f"{features['late_payment_rate']:.0f}% late payments"
        
        if features['payment_gaps'] > 1:
            risks['missed_payments'] = f"{features['payment_gaps']} missed months"
        
        # Engagement risks
        if features['engagement_score'] < 30:
            risks['low_engagement'] = 'Overall low engagement score'
        
        return risks
    
    def predict_all_members(self, members: List[Dict]) -> List[Dict]:
        """
        Predict churn for all members and return at-risk list
        
        Returns:
            List of members with churn predictions, sorted by risk
        """
        predictions = []
        
        for member in members:
            try:
                churn_prob, risk_factors = self.predict_churn(member)
                
                predictions.append({
                    'member_id': member['id'],
                    'name': member['name'],
                    'phone': member['phone'],
                    'email': member.get('email'),
                    'churn_probability': churn_prob * 100,  # Convert to percentage
                    'risk_level': self._get_risk_level(churn_prob),
                    'risk_factors': risk_factors,
                    'tenure_months': (datetime.now().date() - datetime.strptime(member['joined_date'], '%Y-%m-%d').date()).days / 30
                })
            except Exception as e:
                print(f"Error predicting churn for member {member.get('id')}: {e}")
        
        # Sort by churn probability (highest first)
        predictions.sort(key=lambda x: x['churn_probability'], reverse=True)
        
        return predictions
    
    def _get_risk_level(self, churn_prob: float) -> str:
        """Categorize risk level"""
        if churn_prob >= 0.7:
            return 'CRITICAL'
        elif churn_prob >= 0.5:
            return 'HIGH'
        elif churn_prob >= 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def save_model(self):
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names
        }, self.model_path)
        print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from disk"""
        data = joblib.load(self.model_path)
        self.model = data['model']
        self.feature_names = data['feature_names']
        print(f"Model loaded from {self.model_path}")
