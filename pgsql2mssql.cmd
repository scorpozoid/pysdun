@echo off
rem
rem
rem * remove default for domains
rem * text to varchar(max)
rem * mask_caption - varchar(max) -> t_longstring
rem * dvbsaview - [interval] naming conflict
rem * поля в кавычках ("interval", "offset") - не парсятся
rem * 

cls

set HOME=C:\home\%USERNAME%
set HOMEBIN=%HOME%\bin
rem set PATH=%HOMEBIN%\python-3.6.5;%PATH%
set PATH=%HOMEBIN%\python-3.2.5.1\App;%PATH%
set PATH=%HOMEBIN%\python-2.7.5.1\App;%PATH%
set PATH=%PATH%;%HOMEBIN%\postgresql-9.4.15\x32\bin
set PATH=%PATH%;%HOMEBIN%\aoo-2018.03.21
set PATH=%PATH%;C:\Program Files\PostgreSQL\9.4\bin
set PATH=%PATH%;C:\Program Files (x86)\PostgreSQL\9.4\bin

set TIMESTAMP=0000-00-00

ver | find "6.1" > nul
if %ERRORLEVEL% == 0 chcp 65001

for /f "delims=" %%A in ('aoogen date --minus') do set "TIMESTAMP=%%A"

set PATH=%PATH%;%HOME%\devel\prj\pysdun
set DB2BACKUP=dfpostdb
set BACKUPDIR=%HOME%\devel\prj\pysdun
set SCHEMADUMP=%BACKUPDIR%\%TIMESTAMP%-%DB2BACKUP%-pgsql-01.schema 
set MSSQLSCHEMA=%BACKUPDIR%\%TIMESTAMP%-%DB2BACKUP%-mssql-01.sql 

set LC_MESSAGES=en_US.UTF-8
set PGHOST=127.0.0.1
set PGHOSTADDR=127.0.0.1
set PGPORT=5432
set PGUSER=postgres
set PGPASSWORD=masterkey
set PGCLIENTENCODING=UTF8

echo Dump scheme...
pg_dump -d %DB2BACKUP% --schema=public --no-owner --no-privileges --schema-only -f %SCHEMADUMP%

python pgsql2mssql.py -i %SCHEMADUMP% -o %MSSQLSCHEMA%

pause

rem EOF