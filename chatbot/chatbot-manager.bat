@echo off
chcp 65001 >nul
color 0A
title Chatbot Application Manager

:main_menu
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  🤖 CHATBOT APPLICATION MANAGER 🤖           ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║  📱 APPLICATION CONTROL:                                     ║
echo ║    1. 🚀 Start Application                                   ║
echo ║    2. ⏹️  Stop Application                                    ║
echo ║    3. 🔄 Restart Application                                 ║
echo ║                                                              ║
echo ║  🧹 CLEANUP OPTIONS:                                         ║
echo ║    4. 🗑️  Basic Cleanup (Keep Images)                       ║
echo ║    5. 🔥 Full Cleanup (Remove Images)                       ║
echo ║                                                              ║
echo ║    0. ❌ Exit                                                ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
set /p choice="👉 Choose an option (0-5): "

if "%choice%"=="0" goto :exit
if "%choice%"=="1" goto :start_app
if "%choice%"=="2" goto :stop_app
if "%choice%"=="3" goto :restart_app
if "%choice%"=="4" goto :cleanup_basic
if "%choice%"=="5" goto :cleanup_full

echo.
echo ❌ Invalid choice. Please try again.
timeout /t 2 >nul
goto :main_menu

:start_app
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🚀 STARTING APPLICATION                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Docker is not running or not installed.
    echo 💡 Please start Docker Desktop and try again.
    echo.
    pause
    goto :main_menu
)

REM Navigate to the directory containing docker-compose.yml
cd /d "%~dp0"

echo 🔄 Starting Docker Compose services...
echo    ⏳ First startup may take several minutes...
echo.
docker-compose up -d >nul

if %errorlevel% equ 0 (
    echo.
    echo ✅ Chatbot application started successfully!
    echo.
    echo 🌐 Access the application at: http://localhost
    echo 💡 Keep this window open to manage the app.
) else (
    echo.
    echo ❌ Failed to start the application.
    echo 💡 Check Docker Desktop and try again.
)

echo.
pause
goto :main_menu

:stop_app
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     ⏹️ STOPPING APPLICATION                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Docker is not running or not installed.
    pause
    goto :main_menu
)

cd /d "%~dp0"

echo 🔄 Stopping Docker Compose services...
docker-compose down >nul

if %errorlevel% equ 0 (
    echo.
    echo ✅ Chatbot application stopped successfully!
    echo.
    echo 📝 All containers have been stopped and removed.
    echo 💾 Data volumes are preserved for next startup.
) else (
    echo.
    echo ❌ Failed to stop the application completely.
    echo 💡 Some containers might still be running.
    echo    You can check manually with: docker ps
)

echo.
pause
goto :main_menu

:restart_app
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                   🔄 RESTARTING APPLICATION                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Docker is not running or not installed.
    pause
    goto :main_menu
)

cd /d "%~dp0"

echo 🔄 Stopping application...
docker-compose down >nul
echo.
echo 🚀 Starting application...
docker-compose up -d >nul

if %errorlevel% equ 0 (
    echo.
    echo ✅ Application restarted successfully!
    echo 🌐 Access at: http://localhost
) else (
    echo.
    echo ❌ Restart failed. Check logs for details.
)

echo.
pause
goto :main_menu

:cleanup_basic
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🗑️ BASIC CLEANUP                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo ⚠️  This will remove:
echo    • All containers
echo    • All networks  
echo    • All data volumes (DATABASE WILL BE LOST!)
echo.
echo ✅ This will keep:
echo    • Docker images (for faster restart)
echo.
set /p confirm="❓ Continue with basic cleanup? (y/N): "
if /i not "%confirm%"=="y" goto :main_menu

cd /d "%~dp0"
echo.
echo 🗑️ Stopping all containers first...
docker-compose down >nul
echo 🗑️ Removing containers, networks, and volumes...
docker-compose down -v --remove-orphans >nul

echo.
echo ✅ Basic cleanup completed!
echo 💡 Images preserved for faster next startup.
echo.
pause
goto :main_menu

:cleanup_full
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     🔥 FULL CLEANUP                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo ⚠️  This will remove:
echo    • All containers
echo    • All networks
echo    • All data volumes (DATABASE WILL BE LOST!)
echo    • All project Docker images
echo.
set /p confirm="❓ Continue with full cleanup? (y/N): "
if /i not "%confirm%"=="y" goto :main_menu

cd /d "%~dp0"
echo.
echo 🗑️ Stopping all containers first...
docker-compose down >nul
echo 🗑️ Removing containers, networks, and volumes...
docker-compose down -v --remove-orphans >nul

echo 🗑️ Removing project images...
docker rmi longtch/chatbot-client >nul 2>nul
docker rmi longtch/chatbot-server >nul 2>nul  
docker rmi longtch/chatbot-nginx >nul 2>nul
docker rmi groonga/pgroonga:4.0.1-alpine-17 >nul 2>nul
docker rmi qdrant/qdrant >nul 2>nul

echo.
echo ✅ Full cleanup completed!
echo 💡 Next startup will download fresh images.
echo.
pause
goto :main_menu

:exit
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                        👋 GOODBYE!                           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🙏 Thank you for using Chatbot Application Manager!
echo.
timeout /t 2 >nul
exit /b 0
