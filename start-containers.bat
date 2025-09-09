@echo off
echo Starting MCP Server Test Project Containers...
echo.

:: Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running or not installed!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Building and starting all containers...
docker-compose up --build -d

echo.
echo Waiting for services to start...
timeout /t 10 >nul

echo.
echo ================================================
echo MCP Server Test Project Started Successfully!
echo ================================================
echo.
echo Services available at:
echo - Frontend (React): http://localhost:3000
echo - Backend API: http://localhost:8002
echo - ChromaDB Viewer: http://localhost:8080  
echo - ChromaDB Database: http://localhost:8001
echo - MinIO Console: http://localhost:9001
echo   Username: admin
echo   Password: minio123456
echo.
echo To view logs: docker-compose logs -f
echo To stop containers: docker-compose down
echo.
pause