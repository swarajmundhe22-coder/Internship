import sys, os
sys.path.insert(0, os.path.abspath('.'))

from app.algorithms.recommendations import prevention_recommendation
from app.algorithms.global_corrosion_model import compute_risk_score, MaterialCalibration, RegionCalibrationPack

class DummyPoint:
    def __init__(self, oh, cr, risk):
        self.offset_hours = oh
        self.corrosion_rate_mm_per_year = cr
        self.risk_classification = risk

from app.services.prediction_service import PredictionService

print("====================================")
print("--- RECOMMENDATION (HIGH) ---")
print(prevention_recommendation("high"))

print("\n--- SUMMARY (LOW to CRITICAL) ---")
ps = PredictionService()
timeline = [DummyPoint(0, 0.1, "LOW"), DummyPoint(17520, 0.45, "CRITICAL")]
print(ps._build_summary(timeline, "LOW"))
print("====================================")
