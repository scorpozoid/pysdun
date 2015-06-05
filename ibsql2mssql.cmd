@echo off
rem
rem
rem

cls

set HOME=C:\home\ark
set PATH=%PATH%;%HOME%\bin\python-2.7.6.1\App
set PATH=%PATH%;%HOME%\devel\shell\devel

ver | find "6.1" > nul
if %ERRORLEVEL% == 0 chcp 65001 

set PROJ=%HOME%\devel\nig\dfpost\418

rem # - 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem set IBESCRIPT=%PROJ%\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
set IBESCRIPT=%PROJ%\trunk\DFLib\DataBase\DatabaseSrc\dfpostdb\ib\dfpostdb-ib.sql
set MSGSCRIPTMAIN=%PROJ%\trunk\DFLib\DataBase\DatabaseSrc\dfpostdb\mssql\dfpostdb-mssql.sql
set MSGSCRIPTSP=%PROJ%\trunk\DFLib\DataBase\DatabaseSrc\dfpostdb\mssql\dfpostdb-mssql-proc.sql
set MSGSCRIPTTR=%PROJ%\trunk\DFLib\DataBase\DatabaseSrc\dfpostdb\mssql\dfpostdb-mssql-triggers.sql
set MSGSCRIPTTEST01=%PROJ%\trunk\DFLib\DataBase\DatabaseSrc\dfpostdb\mssql\dfpostdb-mssql-test-01.sql
set MSGSCRIPTTEST02=%PROJ%\trunk\DFLib\DataBase\DatabaseSrc\dfpostdb\mssql\dfpostdb-mssql-test-02.sql

python ibsql2mssql.py -i %IBESCRIPT% -o %MSGSCRIPTMAIN%

rem # /* EOF */
