@echo off
REM ==============================================================================
REM Inspect Integrated Indian Road Damage Datasets (TXT, COCO, VOC)
REM ==============================================================================
echo [INFO] Inspecting Indian Road Damage Datasets at E:\IOT project\data...
python "E:\IOT project\branches\branch-02-vision-yolov8-rdd2022\scripts\rdd_dataset_loader.py"
echo.
echo [INFO] Annotated sample previews saved to: E:\IOT project\data\sample_previews\
pause
