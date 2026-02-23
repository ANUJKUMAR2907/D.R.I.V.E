@echo off
setlocal

echo 🚦 D.R.I.V.E - Dynamic Road Intelligence & Vehicle Environment
echo ==============================================================

if "%1"=="" goto all
if "%1"=="all" goto all
if "%1"=="backend" goto backend
if "%1"=="frontend" goto frontend
if "%1"=="simulation" goto simulation
if "%1"=="surveillance" goto surveillance
if "%1"=="dashboard" goto dashboard
if "%1"=="camera" goto camera

:all
echo Starting All Services...
start "Backend API" cmd /k "cd backend && echo Installing deps... && pip install -r requirements.txt && python main.py"
timeout /t 2
start "Surveillance Server" cmd /k "cd surveillance && echo Installing deps... && pip install -r requirements.txt && python server_aggregator.py"
timeout /t 1
start "Frontend" cmd /k "cd frontend && echo Installing deps... && npm install && npm run dev"
timeout /t 2
start "Dashboard" cmd /k "cd dashboard && echo Installing deps... && pip install -r requirements.txt && streamlit run app.py"
goto end

:backend
echo Starting Backend Only...
cd backend
pip install -r requirements.txt
python main.py
goto end

:frontend
echo Starting Frontend Only...
cd frontend
npm install
npm run dev
goto end

:simulation
echo Starting SUMO Simulation...
cd simulation
pip install -r requirements.txt
python controller.py --gui
goto end

:surveillance
echo Starting Surveillance Server...
cd surveillance
pip install -r requirements.txt
python server_aggregator.py
goto end

:camera
if "%2"=="" (set CAM_ID=CAM001) else (set CAM_ID=%2)
echo Starting Camera Client (%CAM_ID%)...
cd surveillance
pip install -r requirements.txt
python client_camera.py --camera-id %CAM_ID% --server http://localhost:5001
goto end

:dashboard
echo Starting Dashboard...
cd dashboard
pip install -r requirements.txt
streamlit run app.py
goto end

:end
echo Done.
endlocal
