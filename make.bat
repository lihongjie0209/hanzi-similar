@echo off
REM Makefile-like script for hanzi-similar project

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="build" goto build
if "%1"=="push" goto push
if "%1"=="run" goto run
if "%1"=="test" goto test
if "%1"=="clean" goto clean
goto help

:help
echo.
echo Hanzi-Similar Project Commands
echo ==============================
echo.
echo Usage: make.bat [command]
echo.
echo Commands:
echo   build     - Build Docker image using current git tag
echo   push      - Build and push Docker image to registry
echo   run       - Run the API server locally
echo   test      - Run API tests
echo   clean     - Clean up Docker images
echo   help      - Show this help message
echo.
goto end

:build
echo Building Docker image...
call build-docker.bat
goto end

:push
echo Building and pushing Docker image...
call build-docker.bat --push
goto end

:run
echo Starting API server...
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo Starting uvicorn server...
uvicorn api_main:app --host 127.0.0.1 --port 8001 --reload
goto end

:test
echo Running API tests...
call .venv\Scripts\activate.bat
python test_batch_api.py
goto end

:clean
echo Cleaning up Docker images...
for /f "tokens=3" %%i in ('docker images lihongjie0209/hanzi-similar -q') do docker rmi %%i
echo Cleaning up dangling images...
docker image prune -f
goto end

:end
