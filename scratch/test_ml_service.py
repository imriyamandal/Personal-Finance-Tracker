import os
import sys

# Add database, services, and ml directories based on current working directory
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "backend", "app", "database")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "ml")))
sys.path.append(os.path.abspath(os.getcwd()))

import db_manager
import ml_service

def test_ml_pipeline():
    print("Initializing database...")
    db_manager.initialize_db()
    user_id = 1
    
    # 1. Test category prediction with fallback
    print("Testing ML category prediction...")
    pred1 = ml_service.predict_category("taxi ride to office", "Expense", user_id)
    print(f"  |--> Predicted 'taxi ride to office' -> {pred1}")
    assert pred1 == "Transport", "Should map taxi to Transport"
    
    pred2 = ml_service.predict_category("Monthly office salary", "Income", user_id)
    print(f"  |--> Predicted 'Monthly office salary' -> {pred2}")
    assert pred2 == "Salary", "Should map salary to Salary"
    
    # 2. Test expense forecast
    print("Testing Linear Regression expense forecast...")
    forecast = ml_service.predict_monthly_spending(user_id)
    print(f"  |--> Forecasted spending: ${forecast:.2f}")
    assert forecast >= 0.0, "Forecast should be non-negative"
    
    # 3. Test anomaly detection
    print("Testing statistical anomaly detection...")
    anomalies = ml_service.detect_anomalies(user_id)
    print(f"  |--> Found {len(anomalies)} anomalies.")
    for idx, a in enumerate(anomalies, 1):
        print(f"      {idx}. Outlier: ${a['amount']:.2f} on {a['date']} (Cat Avg: ${a['category_average']:.2f})")
        
    # 4. Test personalized advice cards
    print("Testing recommendations generator...")
    recs = ml_service.generate_recommendations(user_id)
    print(f"  |--> Generated {len(recs)} advice cards:")
    for idx, r in enumerate(recs, 1):
        print(f"      {idx}. {r}")
        
    assert len(recs) > 0, "Should generate at least one advice recommendation card"
    print("\nMachine Learning Pipeline programmatic verification passed successfully!")

if __name__ == "__main__":
    test_ml_pipeline()
