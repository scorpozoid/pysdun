@echo off
rem
rem
rem

cls

set HOME=C:\home\ark
set PATH=%PATH%;%HOME%\bin\python-2.7.6.1\App
set PATH=%PATH%;%HOME%\bin\python-3.2.1.1\App
set PATH=%PATH%;%HOME%\devel\shell\devel

set PGCLIENTENCODING=utf-8 
rem set PGCLIENTENCODING=WIN  
rem set PGCLIENTENCODING=WIN1251
chcp 65001 
set PGOPTIONS=--client-min-messages=warning
rem # [i] debug w/echo: -e
rem # [w] Don't use &PGHOST & $PGUSER variables here: -h %PGHOST% -U %PGUSER% -n -v ON_ERROR_STOP=1
set PGPSQL_OPTS=-n -v ON_ERROR_STOP=1 -q


set PROJ418=%HOME%\devel\nig\dfpost\418
set PROJ419=%HOME%\devel\nig\dfpost\419
set PROJXE3=%HOME%\devel\nig\dfpost\xe3


rem # --
rem # -- 8.2 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem # --
set PGUSER=postgres
set PGPASSWORD=postgres
rem set PGPASSWORD=masterkey
set PGHOST=192.168.47.34
rem set PGHOSTADDR=192.168.47.134
set PGPSQL_EXE="%HOME%\bin\pgAdmin III 1.10.5\psql.exe" 
set PGPSQL=%PGPSQL_EXE% %PGPSQL_OPTS%

rem # - 8.2 / 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set IBESCRIPT418=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
set PGSCRIPT418MAIN=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql.sql
set PGSCRIPT418SP=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-proc.sql
set PGSCRIPT418TR=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-triggers.sql
set DB418=dfpostdb418
python ibsql2pgsql.py -i %IBESCRIPT418% -o %PGSCRIPT418MAIN%
%PGPSQL% -c "drop database %DB418%"
%PGPSQL% -c "create database %DB418%"
%PGPSQL% -d %DB418% -c "create language 'plpgsql'"
%PGPSQL% -d %DB418% -f %PGSCRIPT418MAIN%
%PGPSQL% -d %DB418% -f %PGSCRIPT418SP%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TR%
echo "FIN: 8.2/4.1.8"
pause
rem exit /b

rem # - 8.2 / 4.1.9 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set IBESCRIPT419=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
set PGSCRIPT419MAIN=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql.sql
set PGSCRIPT419SP=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-proc.sql
set PGSCRIPT419TR=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-triggers.sql
set DB419=dfpostdb419
python ibsql2pgsql.py -i %IBESCRIPT419% -o %PGSCRIPT419MAIN%
%PGPSQL% -c "drop database %DB419%"
%PGPSQL% -c "create database %DB419%"
%PGPSQL% -d %DB419% -c "create language 'plpgsql'"
%PGPSQL% -d %DB419% -f %PGSCRIPT419MAIN%
%PGPSQL% -d %DB419% -f %PGSCRIPT419SP%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TR%
echo "FIN: 8.2/4.1.9"
pause


rem # --
rem # -- 9.1 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem # --
set PGUSER=postgres
set PGPASSWORD=masterkey
set PGHOSTADDR=192.168.47.38
set PGPSQL_EXE="%HOME%\bin\pgAdmin III 1.20.0\psql.exe" 
set PGPSQL=%PGPSQL_EXE% %PGPSQL_OPTS%

rem # - 9.1 / 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set IBESCRIPT418=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
set PGSCRIPT418MAIN=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql.sql
set PGSCRIPT418SP=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-proc.sql
set PGSCRIPT418TR=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-triggers.sql
set DB418=dfpostdb418
python ibsql2pgsql.py -i %IBESCRIPT418% -o %PGSCRIPT418MAIN%
%PGPSQL% -c "drop database %DB418%"
%PGPSQL% -c "create database %DB418%"
%PGPSQL% -d %DB418% -c "create language 'plpgsql'"
%PGPSQL% -d %DB418% -f %PGSCRIPT418MAIN%
%PGPSQL% -d %DB418% -f %PGSCRIPT418SP%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TR%
echo "FIN: 9.1/4.1.8"
pause

rem # - 9.1 / 4.1.9 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set IBESCRIPT419=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
set PGSCRIPT419MAIN=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql.sql
set PGSCRIPT419SP=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-proc.sql
set PGSCRIPT419TR=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-triggers.sql
set DB419=dfpostdb419
python ibsql2pgsql.py -i %IBESCRIPT419% -o %PGSCRIPT419MAIN%
%PGPSQL% -c "drop database %DB419%"
%PGPSQL% -c "create database %DB419%"
%PGPSQL% -d %DB419% -c "create language 'plpgsql'"
%PGPSQL% -d %DB419% -f %PGSCRIPT419MAIN%
%PGPSQL% -d %DB419% -f %PGSCRIPT419SP%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TR%
echo "FIN: 9.1/4.1.9"
pause

rem # /* EOF */