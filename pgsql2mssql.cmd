@echo off
rem
rem
rem

cls

set HOME=C:\home\%USERNAME%
set PATH=%PATH%;%HOME%\bin\python-2.7.6.1\App
set PATH=%PATH%;%HOME%\devel\shell\devel

rem Path to find pg_dump.exe utility
set PATH=%PATH%;c:\home\%USERNAME%\bin\postgresql-9.4.15\x32\bin
set PATH=%PATH%;C:\Program Files\PostgreSQL\9.4\bin
set PATH=%PATH%;C:\Program Files (x86)\PostgreSQL\9.4\bin
set HOME=C:\home\%USERNAME%
set PATH=%PATH%;%HOME%\bin\python-2.7.6.1\App
set PATH=%PATH%;%HOME%\devel\shell\devel

ver | find "6.1" > nul
if %ERRORLEVEL% == 0 chcp 65001

rem BACKUPDIR - destination folder for backup/dump data
set BACKUPDIR=C:\home\ark\devel\pg2ms
rem DB2BACKUP - database name to backup
set DB2BACKUP=dfpostdb
set SCHEMADUMP=%BACKUPDIR%\%TIMESTAMP%-%DB2BACKUP%-01.schema 
set DATADUMP=%BACKUPDIR%\%TIMESTAMP%-%DB2BACKUP%-02.pgdump 

set lc_messages=en_US.UTF-8

set PGHOST=10.4.0.104
set PGHOSTADDR=10.4.0.104
set PGHOST=127.0.0.1
set PGHOSTADDR=127.0.0.1
set PGPORT=5432
set PGUSER=postgres
set PGPASSWORD=masterkey
set PGCLIENTENCODING=UTF8

echo Dump scheme...
pg_dump -d %DB2BACKUP% --schema=public --no-owner --no-privileges --schema-only -f %SCHEMADUMP%


set PROJ=%HOME%\devel\nig\dfpost\418

rem # - 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem set IBESCRIPT=%PROJ%\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
set PGSCHEMADUMP=%SCHEMADUMP%
set MSGSCRIPTMAIN=%SCHEMADUMP%-mssql

set MSGSCRIPTTEST01=%PROJ%\trunk\DFLib\DataBase\DatabaseSrc\dfpostdb\mssql\dfpostdb-mssql-test-01.sql
set MSGSCRIPTTEST02=%PROJ%\trunk\DFLib\DataBase\DatabaseSrc\dfpostdb\mssql\dfpostdb-mssql-test-02.sql

python pgsql2mssql.py -i %PGSCHEMADUMP% -o %MSGSCRIPTMAIN%

rem # /* EOF */
