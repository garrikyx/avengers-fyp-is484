@echo off
rem UBS-134: open every Day-1 demo component in its own visible window (Windows).
rem
rem   scripts\demo_windows.bat              start everything (default)
rem   scripts\demo_windows.bat alerts       table of every alert so far (rule, severity, status, first seen)
rem   scripts\demo_windows.bat burst        60%% rejects: HighRejectRate, RejectSpike, AbnormalRejectRate, AbnormalExecutionIssueRate
rem   scripts\demo_windows.bat normal       back to 0.5%% rejects: those alerts resolve
rem   scripts\demo_windows.bat app-fault    OutOfMemoryError lines in Application.log: AppOutOfMemory, AppLogFailure
rem   scripts\demo_windows.bat app-normal   no more fault lines: those alerts resolve
rem   scripts\demo_windows.bat logs-stop    close the log generator: NoLogActivity
rem   scripts\demo_windows.bat logs-start   reopen it with the same settings
rem   scripts\demo_windows.bat agent-stop   close the agent window: AgentHeartbeatMissing
rem   scripts\demo_windows.bat agent-start  start the agent again (resumes from saved offsets)
rem   scripts\demo_windows.bat stop         close every demo window
rem
rem Same entrypoints and config/demo/* as scripts/demo.py; local hosting only.
rem The guided, self-checking version is still: uv run python -m scripts.demo
setlocal EnableExtensions
cd /d "%~dp0.."
set "ROOT=%CD%"
set "RUN=%ROOT%\.demo-run"
set "VENV=%ROOT%\.venv\Scripts"
set "TITLE=FYP demo"
set "BACKEND=http://127.0.0.1:8080"

rem Simulator settings. They are saved in the run folder so every restart
rem (burst, app-fault, logs-start, ...) keeps the other setting.
set "NORMAL_RATE=0.005"
set "BURST_RATE=0.6"
set "FAULT_RATE=0.05"

rem Dev-only values, the same fallbacks as .env.example and scripts/demo.py.
set "MAGIC_TELEMETRY_ID_HASH_KEY=dev-only"
set "MAGIC_TELEMETRY_PUBLISH_TOKEN=dev-local-token"
set "MAGIC_TELEMETRY_CALLBACK_SECRET=dev-local-secret"
set "TELEMETRY_BACKEND_URL=%BACKEND%"
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"

set "CMD=%~1"
if "%CMD%"=="" set "CMD=start"
if /i "%CMD%"=="start" goto start
if /i "%CMD%"=="stop" goto stop
if /i "%CMD%"=="alerts" goto alerts
if /i "%CMD%"=="burst" (set "NEW_RATE=%BURST_RATE%" & goto sim_restart)
if /i "%CMD%"=="normal" (set "NEW_RATE=%NORMAL_RATE%" & goto sim_restart)
if /i "%CMD%"=="app-fault" (set "NEW_FAULTS=%FAULT_RATE%" & goto sim_restart)
if /i "%CMD%"=="app-normal" (set "NEW_FAULTS=0" & goto sim_restart)
if /i "%CMD%"=="logs-stop" goto logs_stop
if /i "%CMD%"=="logs-start" goto logs_start
if /i "%CMD%"=="agent-stop" goto agent_stop
if /i "%CMD%"=="agent-start" goto agent_start
echo Unknown command "%CMD%".
echo Use: start, alerts, burst, normal, app-fault, app-normal, logs-stop, logs-start, agent-stop, agent-start, stop.
exit /b 2

rem ---------------------------------------------------------------------------
:start
echo === Preflight ===
call uv sync --all-packages || (echo uv sync failed & exit /b 1)
set "BUSY="
for %%P in (8080 8081 9000 3978 8765) do (
  netstat -ano | findstr /R /C:":%%P .*LISTENING" >nul && call set "BUSY=%%BUSY%% %%P"
)
if defined BUSY (
  echo Ports already in use:%BUSY%
  echo Run "scripts\demo_windows.bat stop" or close the old windows first.
  exit /b 1
)
powershell -NoProfile -Command "try { $m = (Invoke-RestMethod http://127.0.0.1:11434/api/tags -TimeoutSec 2).models.name; if ($m -contains 'llama3.2') { 'Ollama: llama3.2 available' } else { 'WARNING: config/demo/backend.yaml asks Ollama for llama3.2, but it has: ' + ($m -join ', ') + '. Free-form questions will get the fallback reply; the headline question is rule-matched and still answers.' } } catch { 'Ollama not running: rule-matched questions (the headline question) still answer.' }"
if exist "%RUN%" rmdir /s /q "%RUN%"
mkdir "%RUN%\logs"
echo Fresh run folder: %RUN%
call :save_sim %NORMAL_RATE% 0

echo === 1. Backend :8080 ===
start "%TITLE%: 1 backend :8080" /D "%ROOT%" cmd /k ""%VENV%\telemetry-backend.exe" --config config\demo\backend.yaml"
call :wait_http %BACKEND%/healthz "backend /healthz" || exit /b 1

echo === 2. Magic callback STUB :9000 ===
start "%TITLE%: 2 Magic callback STUB :9000" /D "%ROOT%" cmd /k ""%VENV%\python.exe" -m scripts.mock_magic_callback_receiver --record "%RUN%\callbacks.jsonl""
call :wait_port 9000 "Magic stub" || exit /b 1

echo === 3. Simulator (log generator) ===
call :start_simulator

echo === 4. Agent ===
call :start_agent

echo === 5. Teams bot :3978 ===
start "%TITLE%: 5 Teams bot :3978" /D "%ROOT%" cmd /k "set "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=00000000-0000-0000-0000-000000000000"&& set "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=dummy"&& set "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=00000000-0000-0000-0000-000000000000"&& set "CONNECTIONS__SERVICE_CONNECTION__SETTINGS__ANONYMOUS_ALLOWED=true"&& "%VENV%\telemetry-teams.exe""
call :wait_port 3978 "Teams bot" || exit /b 1

echo === 6. MCP server for Copilot :8765 ===
start "%TITLE%: 6 MCP server (Copilot) :8765" /D "%ROOT%" cmd /k ""%VENV%\telemetry-mcp.exe""
call :wait_port 8765 "MCP server" || exit /b 1

echo === 7. Teams App Test Tool (playground) ===
rem set DEMO_SKIP_TEST_TOOL=1 to skip this window (e.g. when showing Copilot only).
if defined DEMO_SKIP_TEST_TOOL (echo   skipped: DEMO_SKIP_TEST_TOOL is set) else start "%TITLE%: 7 Teams App Test Tool" /D "%ROOT%" cmd /k "npx -y @microsoft/teams-app-test-tool start -e http://localhost:3978/api/messages -c msteams"

echo.
echo All windows started. Ask the Test Tool: "Why are Magic orders rejecting in the last 30 minutes?"
echo Copilot / MCP Inspector: http://127.0.0.1:8765/mcp
echo.
echo Let normal trading run for 3+ minutes before "burst": the anomaly rules
echo (AbnormalRejectRate, AbnormalExecutionIssueRate) need that baseline.
echo Next: scripts\demo_windows.bat alerts ^| burst ^| normal ^| app-fault ^| app-normal ^| logs-stop ^| logs-start ^| agent-stop ^| agent-start ^| stop
exit /b 0

rem ---------------------------------------------------------------------------
:sim_restart
call :load_sim
if defined NEW_RATE set "RATE=%NEW_RATE%"
if defined NEW_FAULTS set "FAULTS=%NEW_FAULTS%"
call :save_sim %RATE% %FAULTS%
call :close "3 simulator"
call :start_simulator
echo Simulator restarted: reject rate %RATE%, app faults %FAULTS%.
if /i "%CMD%"=="burst" echo Expect HighRejectRate and RejectSpike in ~15 s, the Abnormal* rules in ~15-30 s (after a 3 min baseline).
if /i "%CMD%"=="normal" echo Expect the reject alerts to step down and resolve in ~1-2 min.
if /i "%CMD%"=="app-fault" echo Expect AppOutOfMemory and AppLogFailure within a few seconds.
if /i "%CMD%"=="app-normal" echo Expect AppOutOfMemory and AppLogFailure to resolve once the 1 min window clears.
exit /b 0

:logs_stop
call :close "3 simulator"
echo Log generator stopped. NoLogActivity should fire once a full minute has no new lines.
exit /b 0

:logs_start
call :start_simulator
echo Log generator restarted. NoLogActivity resolves once lines arrive again.
exit /b 0

:agent_stop
rem Closing the window sends Ctrl+Close; the agent treats it like Ctrl+Break
rem (SIGBREAK): drain, publish, checkpoint offsets, then exit.
call :close "4 agent"
echo Agent stopped. AgentHeartbeatMissing should fire in about 20-30 s.
exit /b 0

:agent_start
call :start_agent
echo Agent started again from its saved offsets.
exit /b 0

:alerts
powershell -NoProfile -Command "try { $r = Invoke-RestMethod '%BACKEND%/telemetry/alerts?status=all&limit=50' } catch { 'Backend not reachable on %BACKEND%.'; exit 1 }; if (-not $r.alerts) { 'No alerts yet.' } else { $r.alerts | Select-Object ruleName, severity, status, @{n='observed';e={$_.observedValue}}, threshold, @{n='firstSeen';e={([datetime]$_.firstObservedUtc).ToLocalTime().ToString('HH:mm:ss')}}, @{n='resolved';e={if ($_.resolvedAtUtc) { ([datetime]$_.resolvedAtUtc).ToLocalTime().ToString('HH:mm:ss') } else { '' }}} | Format-Table -AutoSize | Out-String -Width 200; 'Active: ' + $r.counts.active + '  (critical ' + $r.counts.critical + ', warning ' + $r.counts.warning + ')' }"
exit /b 0

:stop
for %%W in ("7 Teams App Test Tool" "6 MCP" "5 Teams bot" "4 agent" "3 simulator" "2 Magic" "1 backend") do call :close %%W
echo All demo windows closed.
exit /b 0

rem ---------------------------------------------------------------------------
:start_simulator
if not exist "%RUN%\logs" (echo No run folder; run "scripts\demo_windows.bat" first. & exit /b 1)
call :load_sim
start "%TITLE%: 3 simulator" /D "%RUN%" cmd /k ""%VENV%\python.exe" "%ROOT%\apps\simulator\src\simulator\mock_logger.py" --interval 0.05 --max-bytes 100000 --reject-rate %RATE% --app-faults %FAULTS%"
exit /b 0

:start_agent
if not exist "%RUN%\logs" (echo No run folder; run "scripts\demo_windows.bat" first. & exit /b 1)
start "%TITLE%: 4 agent" /D "%RUN%" cmd /k ""%VENV%\telemetry-agent.exe" --config "%ROOT%\config\demo\agent.yaml""
exit /b 0

:load_sim
set "RATE=%NORMAL_RATE%"
set "FAULTS=0"
if exist "%RUN%\sim-rate.txt" set /p RATE=<"%RUN%\sim-rate.txt"
if exist "%RUN%\sim-faults.txt" set /p FAULTS=<"%RUN%\sim-faults.txt"
exit /b 0

:save_sim
>"%RUN%\sim-rate.txt" echo %~1
>"%RUN%\sim-faults.txt" echo %~2
exit /b 0

:close
rem %1 = window title prefix. cmd adds " - <command>" while it runs.
taskkill /T /FI "WINDOWTITLE eq %TITLE%: %~1*" >nul 2>&1
call :sleep 3
taskkill /T /F /FI "WINDOWTITLE eq %TITLE%: %~1*" >nul 2>&1
exit /b 0

:wait_http
for /l %%i in (1,1,60) do (
  curl -sf %1 >nul 2>&1 && (echo   %~2 is up & exit /b 0)
  call :sleep 1
)
echo   %~2 did not come up in 60 s; check its window.
exit /b 1

:wait_port
for /l %%i in (1,1,60) do (
  netstat -ano | findstr /R /C:":%1 .*LISTENING" >nul && (echo   %~2 is listening on :%1 & exit /b 0)
  call :sleep 1
)
echo   %~2 did not listen on :%1 in 60 s; check its window.
exit /b 1

:sleep
rem ping instead of timeout: timeout fails when stdin is redirected.
set /a "_n=%~1+1"
ping -n %_n% 127.0.0.1 >nul
exit /b 0
