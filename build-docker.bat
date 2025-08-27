@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Docker Build and Push Script
echo Using Git Tags for Versioning
echo ========================================

REM Get current git tag
for /f "tokens=*" %%i in ('git describe --tags --exact-match HEAD 2^>nul') do set CURRENT_TAG=%%i

if "%CURRENT_TAG%"=="" (
    echo Warning: Current HEAD is not on a tag, trying to get latest tag...
    for /f "tokens=*" %%i in ('git describe --tags --abbrev=0 2^>nul') do set CURRENT_TAG=%%i
    if "!CURRENT_TAG!"=="" (
        echo Error: No git tags found, please create a tag first
        exit /b 1
    )
    echo Using latest tag: !CURRENT_TAG!
) else (
    echo Current tag: %CURRENT_TAG%
)

set VERSION=%CURRENT_TAG%
set REGISTRY=lihongjie0209
set IMAGE_NAME=hanzi-similar
set FULL_IMAGE_NAME=%REGISTRY%/%IMAGE_NAME%

echo.
echo Building Docker image...
echo Version: %VERSION%
echo Image name: %FULL_IMAGE_NAME%
echo.

REM Build Docker image
echo Building Docker image...
docker build -t %IMAGE_NAME% .
if %ERRORLEVEL% neq 0 (
    echo Error: Docker build failed
    exit /b 1
)
echo Success: Docker image built

REM Tag with version
echo Tagging with version: %VERSION%
docker tag %IMAGE_NAME% "%FULL_IMAGE_NAME%:%VERSION%"
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to tag with version
    exit /b 1
)

REM Tag with latest
echo Tagging with latest
docker tag %IMAGE_NAME% "%FULL_IMAGE_NAME%:latest"
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to tag with latest
    exit /b 1
)

echo Success: All tags added
echo.
echo Available image tags:
docker images %FULL_IMAGE_NAME%

REM Check if push is requested
if "%1"=="--push" (
    echo.
    echo Pushing images to remote registry...
    
    echo Pushing version tag: %VERSION%
    docker push "%FULL_IMAGE_NAME%:%VERSION%"
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to push version tag - check if you're logged in to Docker Hub
        exit /b 1
    )
    
    echo Pushing latest tag
    docker push "%FULL_IMAGE_NAME%:latest"
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to push latest tag - check if you're logged in to Docker Hub
        exit /b 1
    )
    
    echo.
    echo Success: All images pushed!
    echo Image URLs:
    echo   - %FULL_IMAGE_NAME%:%VERSION%
    echo   - %FULL_IMAGE_NAME%:latest
) else (
    echo.
    echo Images built successfully. Use --push to push to remote registry
    echo Or run manually:
    echo   docker push %FULL_IMAGE_NAME%:%VERSION%
    echo   docker push %FULL_IMAGE_NAME%:latest
)

echo.
echo Script completed successfully!
