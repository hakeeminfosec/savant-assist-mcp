@echo off
echo Starting MinIO and supporting containers...

REM Start all containers in detached mode
docker-compose up -d

echo.
echo Waiting for containers to initialize...
timeout /t 15 /nobreak > nul

echo.
echo ================================================
echo    MinIO Setup Complete!
echo ================================================
echo.
echo MinIO Web UI:       http://localhost:9001
echo   Username: admin
echo   Password: minio123456
echo.
echo MinIO API:          http://localhost:9000
echo ChromaDB:           http://localhost:8001  
echo PostgreSQL:         localhost:5432
echo.
echo Bucket 'documents' created automatically
echo ================================================
echo.
echo To view logs: docker-compose logs -f
echo To stop:      docker-compose down
echo ================================================

pause