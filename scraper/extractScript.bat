@echo off
setlocal

set "COUNT=20"
set "COMMAND=python extractor.py cross-verified-database.csv 1.csv 1"

for /L %%i in (1,1,%COUNT%) do (
    %COMMAND%
)

endlocal