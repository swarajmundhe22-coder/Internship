import pytest
from app.core.optimizer import PredictionOptimizer

def test_platt_scaling_calibration():
    optimizer = PredictionOptimizer()
    
    # Test low raw score
    low_calibrated = optimizer.calibrate_confidence(-2.0)
    assert 0.0 <= low_calibrated <= 1.0
    
    # Test high raw score
    high_calibrated = optimizer.calibrate_confidence(2.0)
    assert 0.0 <= high_calibrated <= 1.0
    
    # Higher raw score should result in higher calibrated confidence given our A/B params
    assert high_calibrated > low_calibrated

def test_bayesian_adjustment():
    optimizer = PredictionOptimizer()
    
    # Low uncertainty, high quality
    low_adj = optimizer.calculate_bayesian_adjustment(0.01, 0.9)
    # High uncertainty, low quality
    high_adj = optimizer.calculate_bayesian_adjustment(0.2, 0.1)
    
    assert high_adj > low_adj
    assert 0.0 <= low_adj <= 0.5
    assert 0.0 <= high_adj <= 0.5

def test_fallback_logic():
    optimizer = PredictionOptimizer()
    
    # Below threshold
    is_fallback, reason = optimizer.apply_fallback_logic(0.90, threshold=0.95)
    assert is_fallback is True
    assert "below threshold" in reason
    
    # Above threshold
    is_fallback, reason = optimizer.apply_fallback_logic(0.98, threshold=0.95)
    assert is_fallback is False
    assert reason is None

def test_performance_evaluation():
    optimizer = PredictionOptimizer()
    
    predictions = [0.95, 0.92, 0.05, 0.08]
    ground_truth = [1.0, 1.0, 0.0, 0.0]
    
    metrics = optimizer.evaluate_model_performance(predictions, ground_truth)
    
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0
    assert metrics["accuracy"] == 1.0
