@echo off
rem 
rem Run AnyLogic Experiment
rem 
setlocal enabledelayedexpansion
chcp 1252 >nul 
set DIR_BACKUP_XJAL=%cd%
cd /D "%~dp0"

rem ----------------------------------

rem echo 1.Check JAVA_HOME

if exist "%JAVA_HOME%\bin\java.exe" (
	set PATH=!JAVA_HOME!\bin;!PATH!
	goto javafound
)

rem echo 2.Check PATH

for /f %%j in ("java.exe") do (
	set JAVA_EXE=%%~$PATH:j
)

if defined JAVA_EXE (
	goto javafound
)

rem echo 3.Check AnyLogic registry

set KEY_NAME=HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\AnyLogic North America

FOR /F "usebackq delims=" %%A IN (`REG QUERY "%KEY_NAME%" 2^>nul`) DO (
	set ANYLOGIC_KEY=%%A
)

if defined ANYLOGIC_KEY (
	FOR /F "usebackq delims=" %%A IN (`REG QUERY "%ANYLOGIC_KEY%" 2^>nul`) DO (
		set ANYLOGIC_VERSION_KEY=%%A
	)	
)

if defined ANYLOGIC_VERSION_KEY (
	FOR /F "usebackq skip=2 tokens=3*" %%A IN (`REG QUERY "%ANYLOGIC_VERSION_KEY%" /v Location 2^>nul`) DO (
		set ANYLOGIC_LOCATION=%%A %%B
	)	
)

if exist "%ANYLOGIC_LOCATION%\jre\bin\java.exe" (
	set PATH=!ANYLOGIC_LOCATION!\jre\bin;!PATH!
	goto javafound 
)

rem echo 4.Check java registry

set KEY_NAME=HKEY_LOCAL_MACHINE\SOFTWARE\JavaSoft\Java Runtime Environment
FOR /F "usebackq skip=2 tokens=3" %%A IN (`REG QUERY "%KEY_NAME%" /v CurrentVersion 2^>nul`) DO (
    set JAVA_CURRENT_VERSION=%%A
)

if defined JAVA_CURRENT_VERSION (
	FOR /F "usebackq skip=2 tokens=3*" %%A IN (`REG QUERY "%KEY_NAME%\%JAVA_CURRENT_VERSION%" /v JavaHome 2^>nul`) DO (
		set JAVA_PATH=%%A %%B
	)
)

if exist "%JAVA_PATH%\bin\java.exe" (
	set PATH=!JAVA_PATH!\bin;!PATH!
	goto javafound
)

rem 32 bit
set KEY_NAME=HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\JavaSoft\Java Runtime Environment
FOR /F "usebackq skip=2 tokens=3" %%A IN (`REG QUERY "%KEY_NAME%" /v CurrentVersion 2^>nul`) DO (
    set JAVA_CURRENT_VERSION=%%A
)

if defined JAVA_CURRENT_VERSION (
	FOR /F "usebackq skip=2 tokens=3*" %%A IN (`REG QUERY "%KEY_NAME%\%JAVA_CURRENT_VERSION%" /v JavaHome 2^>nul`) DO (
		set JAVA_PATH=%%A %%B
	)
)

if exist "%JAVA_PATH%\bin\java.exe" (
	set PATH=!JAVA_PATH!\bin;!PATH!
	goto javafound
)

rem echo 5.Check Program Files
for /f "delims=" %%a in ('dir "%ProgramFiles%\Java\j*" /o-d /ad /b') do (
	set JAVA_PROGRAM_FILES="%ProgramFiles%\Java\%%a"
	if exist "%ProgramFiles%\Java\%%a\bin\java.exe" goto exitloop
)
for /f "delims=" %%a in ('dir "%ProgramFiles(x86)%\Java\j*" /o-d /ad /b') do (
	set JAVA_PROGRAM_FILES="%ProgramFiles(x86)%\Java\%%a"
	if exist "%ProgramFiles(x86)%\Java\%%a\bin\java.exe" goto exitloop
)

:exitloop

if defined JAVA_PROGRAM_FILES (
	set PATH=!JAVA_PROGRAM_FILES!\bin;!PATH!
	goto javafound
)

echo  Error: Java not found
pause 
goto end

:javafound

FOR /F "usebackq tokens=4" %%A IN (`java -fullversion 2^>^&1`) DO (
	set VERSION=%%~A
)

echo Java version: %VERSION%

set OPTIONS_XJAL=--illegal-access=deny
IF "%VERSION:~0,2%"=="1." set OPTIONS_XJAL=

rem ---------------------------

echo on

java %OPTIONS_XJAL% -cp model.jar;lib/MarkupDescriptors.jar;lib/com.anylogic.engine.jar;lib/com.anylogic.engine.nl.jar;lib/com.anylogic.engine.sa.jar;lib/sa/com.anylogic.engine.sa.web.jar;lib/sa/executor-basic-8.3.jar;lib/sa/ioutil-8.3.jar;lib/sa/jackson/jackson-annotations-2.12.2.jar;lib/sa/jackson/jackson-core-2.12.2.jar;lib/sa/jackson/jackson-databind-2.12.2.jar;lib/sa/spark/javax.servlet-api-3.1.0.jar;lib/sa/spark/jetty-client-9.4.31.v20200723.jar;lib/sa/spark/jetty-continuation-9.4.31.v20200723.jar;lib/sa/spark/jetty-http-9.4.31.v20200723.jar;lib/sa/spark/jetty-io-9.4.31.v20200723.jar;lib/sa/spark/jetty-security-9.4.31.v20200723.jar;lib/sa/spark/jetty-server-9.4.31.v20200723.jar;lib/sa/spark/jetty-servlet-9.4.31.v20200723.jar;lib/sa/spark/jetty-servlets-9.4.31.v20200723.jar;lib/sa/spark/jetty-util-9.4.31.v20200723.jar;lib/sa/spark/jetty-webapp-9.4.31.v20200723.jar;lib/sa/spark/jetty-xml-9.4.31.v20200723.jar;lib/sa/spark/slf4j-api-1.7.25.jar;lib/sa/spark/spark-core-2.9.3.jar;lib/sa/spark/websocket-api-9.4.31.v20200723.jar;lib/sa/spark/websocket-client-9.4.31.v20200723.jar;lib/sa/spark/websocket-common-9.4.31.v20200723.jar;lib/sa/spark/websocket-server-9.4.31.v20200723.jar;lib/sa/spark/websocket-servlet-9.4.31.v20200723.jar;lib/sa/util-8.3.jar;lib/database/querydsl/querydsl-core-4.2.1.jar;lib/database/querydsl/querydsl-sql-4.2.1.jar;lib/database/querydsl/querydsl-sql-codegen-4.2.1.jar;lib/database/querydsl/guava-18.0.jar;lib/com.anylogic.rl.data.jar;lib/com.anylogic.rl.connector.support.jar;lib/com.anylogic.rl.connector.bonsai.jar -Xmx512m stock_management_game1.RLExperiment %*

@echo off
if %ERRORLEVEL% neq 0 pause
:end
echo on
@cd /D "%DIR_BACKUP_XJAL%"
