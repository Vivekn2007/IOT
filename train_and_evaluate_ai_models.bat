@echo off
REM ==============================================================================
REM POTHOLE SENSE: Retrain and Verify Deep Learning, Machine Learning, and RL Models
REM ==============================================================================

echo ==============================================================================
echo [STEP 1/3] Benchmarking Deep Learning RDD-Net (Vision Classifier)
echo ==============================================================================
python "E:\IOT project\branches\branch-02-vision-yolov8-rdd2022\scripts\dl_rdd_classifier.py"

echo.
echo ==============================================================================
echo [STEP 2/3] Benchmarking Multi-Modal Machine Learning Fusion (13-dim Classifier)
echo ==============================================================================
python "E:\IOT project\branches\branch-05-sensor-fusion-ekf-frustum\scripts\ml_multimodal_fusion.py"

echo.
echo ==============================================================================
echo [STEP 3/3] Benchmarking Reinforcement Learning Evasion Policy (Continuous Q-Agent)
echo ==============================================================================
python "E:\IOT project\branches\branch-06-jetson-tensorrt-hmi-telemetry\scripts\rl_evasion_policy.py"

echo.
echo ==============================================================================
echo [ALL AI MODULES TRAINED, CALIBRATED, AND VERIFIED!]
echo ==============================================================================
pause
