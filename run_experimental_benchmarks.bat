@echo off
REM ==============================================================================
REM POTHOLE SENSE: Run Genuine Quantitative Experimental Benchmarks Suite
REM ==============================================================================
title Pothole Sense - Empirical Experimental Benchmarks Runner

echo ==============================================================================
echo               POTHOLE SENSE: SCIENTIFIC BENCHMARK SUITE
echo ==============================================================================
echo [*] Executing comprehensive, empirical benchmarks on Indian RDD dataset and CARLA...
echo [*] Evaluating multi-modal sensor fusion, range/depth errors, and edge throughput...
echo.

python "E:\IOT project\run_genuine_experimental_benchmarks.py"

echo.
echo ==============================================================================
echo [UPDATING WORD PROJECT REPORT WITH NEW EXPERIMENTAL FIGURES]
echo ==============================================================================
python "E:\IOT project\build_full_word_report.py"

echo.
echo ==============================================================================
echo [*] Benchmarks finished! Check results in:
echo     - Figures: E:\IOT project\evaluation_figures\
echo     - Report:  E:\IOT project\Complete_BTech_IoT_Project_Report.docx
echo ==============================================================================
pause
