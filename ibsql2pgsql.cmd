@echo off
rem
rem
rem

cls

set HOME=C:\home\ark
set PATH=%PATH%;%HOME%\bin\python-2.7.6.1\App
set PATH=%PATH%;%HOME%\devel\shell\devel

set PGCLIENTENCODING=utf-8 
rem set PGCLIENTENCODING=WIN  
rem set PGCLIENTENCODING=WIN1251

ver | find "6.1" > nul
if %ERRORLEVEL% == 0 chcp 65001 

rem set PGOPTIONS=--client-min-messages=warning
rem # [i] debug w/echo: -e
rem # [w] Don't use &PGHOST & $PGUSER variables here: -h %PGHOST% -U %PGUSER% -n -v ON_ERROR_STOP=1
rem set PGPSQL_OPTS=-n -v ON_ERROR_STOP=1 -q
set PGPSQL_OPTS=-v ON_ERROR_STOP=1

set PROJ418=%HOME%\devel\nig\dfpost\418
set PROJ419=%HOME%\devel\nig\dfpost\419
set PROJXE3=%HOME%\devel\nig\dfpost\xe3

rem # - 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem set IBESCRIPT418=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
rem set PGSCRIPT418MAIN=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql.sql
rem set PGSCRIPT418SP=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-proc.sql
rem set PGSCRIPT418TR=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-triggers.sql
rem set PGSCRIPT418TEST01=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-test-01.sql
rem set PGSCRIPT418TEST02=%PROJ418%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-test-02.sql

set IBESCRIPT418=%PROJ418%\trunk\DFLib\DataBase\db\dfpostdb-ib.sql
set PGSCRIPT418MAIN=%PROJ418%\trunk\DFLib\DataBase\db\dfpostdb-pgsql.sql
set PGSCRIPT418SP=%PROJ418%\trunk\DFLib\DataBase\db\dfpostdb-pgsql-proc.sql
set PGSCRIPT418TR=%PROJ418%\trunk\DFLib\DataBase\db\dfpostdb-pgsql-triggers.sql
set PGSCRIPT418TEST01=%PROJ418%\trunk\DFLib\DataBase\db\dfpostdb-pgsql-test-01.sql
set PGSCRIPT418TEST02=%PROJ418%\trunk\DFLib\DataBase\db\dfpostdb-pgsql-test-02.sql

python ibsql2pgsql.py -i %IBESCRIPT418% -o %PGSCRIPT418MAIN%

exit /b

rem # - 4.1.9 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set IBESCRIPT419=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
set PGSCRIPT419MAIN=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql.sql
set PGSCRIPT419SP=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-proc.sql
set PGSCRIPT419TR=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-triggers.sql
set PGSCRIPT419TEST01=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-test-01.sql
set PGSCRIPT419TEST02=%PROJ419%\trunk\DFLib\DataBase\dfPostDB(PGS)\dfpostdb-pgsql-test-02.sql

rem python ibsql2pgsql.py -i %IBESCRIPT419% -o %PGSCRIPT419MAIN%

rem copy %PGSCRIPT418SP% %PGSCRIPT419SP%
rem copy %PGSCRIPT418TR% %PGSCRIPT419TR%
rem copy %PGSCRIPT418TEST01% %PGSCRIPT419TEST01%
rem copy %PGSCRIPT418TEST02% %PGSCRIPT419TEST02%

rem # --
rem # -- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem # --
rem call :postgresql74
rem call :postgresql93
call :postgresql91
rem call :postgresql82
goto :EOF


:postgresql74
rem # --
rem # -- 7.4 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem # --
set PGHOST=192.168.47.33
set PGHOSTADDR=192.168.47.33
set PGUSER=ark
set PGPASSWORD=ark
rem set PGPASSWORD=masterkey
set PGPSQL_EXE="%HOME%\bin\pgAdmin III 1.10.5\psql.exe" 
set PGPSQL=%PGPSQL_EXE% %PGPSQL_OPTS%

rem # - 7.4 / 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set DB418=dfpostdb418
%PGPSQL% -d template1 -c "drop database %DB418%"
%PGPSQL% -d template1 -c "create database %DB418%"
%PGPSQL% -d %DB418% -c "create language plpgsql"
%PGPSQL% -d %DB418% -f %PGSCRIPT418MAIN%
%PGPSQL% -d %DB418% -f %PGSCRIPT418SP%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TR%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TEST01%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TEST02%
echo "FIN: 7.4/4.1.8 %PGHOST%::%DB418%"
pause

rem # - 7.4 / 4.1.9 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set DB419=dfpostdb419
%PGPSQL% -d template1 -c "drop database %DB419%"
%PGPSQL% -d template1 -c "create database %DB419%"
%PGPSQL% -d %DB419% -c "create language plpgsql"
%PGPSQL% -d %DB419% -f %PGSCRIPT419MAIN%
%PGPSQL% -d %DB419% -f %PGSCRIPT419SP%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TR%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TEST01%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TEST02%
echo "FIN: 7.4/4.1.9 %PGHOST%::%DB419%"
pause
rem exit /b
goto :EOF

:postgresql82
rem # --
rem # -- 8.2 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem # --
set PGHOST=192.168.47.134
set PGHOSTADDR=192.168.47.134
set PGUSER=postgres
set PGPASSWORD=postgres
rem set PGPASSWORD=masterkey
set PGPSQL_EXE="%HOME%\bin\pgAdmin III 1.10.5\psql.exe" 
set PGPSQL=%PGPSQL_EXE% %PGPSQL_OPTS%

rem # - 8.2 / 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set DB418=dfpostdb418
%PGPSQL% -c "drop database %DB418%"
%PGPSQL% -c "create database %DB418%"
%PGPSQL% -d %DB418% -c "create language plpgsql"
%PGPSQL% -d %DB418% -f %PGSCRIPT418MAIN%
%PGPSQL% -d %DB418% -f %PGSCRIPT418SP%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TR%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TEST01%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TEST02%
echo "FIN: 8.2/4.1.8 %PGHOST%::%DB418%"
pause
exit /b

rem # - 8.2 / 4.1.9 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set DB419=dfpostdb419
%PGPSQL% -c "drop database %DB419%"
%PGPSQL% -c "create database %DB419%"
%PGPSQL% -d %DB419% -c "create language plpgsql"
%PGPSQL% -d %DB419% -f %PGSCRIPT419MAIN%
%PGPSQL% -d %DB419% -f %PGSCRIPT419SP%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TR%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TEST01%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TEST02%
echo "FIN: 8.2/4.1.9 %PGHOST%::%DB419%"
pause
rem exit /b
goto :EOF

:postgresql91
rem # --
rem # -- 9.1 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem # --
set PGHOST=192.168.47.38
set PGHOSTADDR=192.168.47.38
set PGUSER=postgres
set PGPASSWORD=masterkey
set PGPSQL_EXE="%HOME%\bin\pgAdmin III 1.20.0\psql.exe" 
set PGPSQL_EXE="C:\Program Files\PostgreSQL\9.1\bin\psql.exe"
set PGPSQL=%PGPSQL_EXE% %PGPSQL_OPTS%

rem # - 9.1 / 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set DB418=dfpostdb418
%PGPSQL% -c "drop database %DB418%"
%PGPSQL% -c "create database %DB418%"
%PGPSQL% -d %DB418% -c "create language 'plpgsql'"
%PGPSQL% -d %DB418% -f %PGSCRIPT418MAIN%
%PGPSQL% -d %DB418% -f %PGSCRIPT418SP%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TR%
rem %PGPSQL% -d %DB418% -f %PGSCRIPT418TEST01%
rem %PGPSQL% -d %DB418% -f %PGSCRIPT418TEST02%
echo "FIN: 9.1/4.1.8 %PGHOST%::%DB418%"
pause
exit /b

rem # - 9.1 / 4.1.9 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set DB419=dfpostdb419
%PGPSQL% -c "drop database %DB419%"
%PGPSQL% -c "create database %DB419%"
%PGPSQL% -d %DB419% -c "create language 'plpgsql'"
%PGPSQL% -d %DB419% -f %PGSCRIPT419MAIN%
%PGPSQL% -d %DB419% -f %PGSCRIPT419SP%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TR%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TEST01%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TEST02%
echo "FIN: 9.1/4.1.9 %PGHOST%::%DB419%"
pause
rem exit /b
goto :EOF

:postgresql93
rem # --
rem # -- 9.3 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
rem # --
set PGHOST=192.168.47.35
set PGHOSTADDR=192.168.47.35
set PGUSER=postgres
set PGPASSWORD=postgres
set PGPSQL_EXE="%HOME%\bin\pgAdmin III 1.20.0\psql.exe" 
set PGPSQL=%PGPSQL_EXE% %PGPSQL_OPTS%

rem # - 9.3 / 4.1.8 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set DB418=dfpostdb418
%PGPSQL% -c "drop database %DB418%"
%PGPSQL% -c "create database %DB418%"
%PGPSQL% -d %DB418% -c "create language 'plpgsql'"
%PGPSQL% -d %DB418% -f %PGSCRIPT418MAIN%
%PGPSQL% -d %DB418% -f %PGSCRIPT418SP%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TR%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TEST01%
%PGPSQL% -d %DB418% -f %PGSCRIPT418TEST02%
echo "FIN: 9.3/4.1.8 %PGHOST%::%DB418%"
pause

rem # - 9.3 / 4.1.9 - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
set DB419=dfpostdb419
%PGPSQL% -c "drop database %DB419%"
%PGPSQL% -c "create database %DB419%"
%PGPSQL% -d %DB419% -c "create language 'plpgsql'"
%PGPSQL% -d %DB419% -f %PGSCRIPT419MAIN%
%PGPSQL% -d %DB419% -f %PGSCRIPT419SP%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TR%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TEST01%
%PGPSQL% -d %DB419% -f %PGSCRIPT419TEST02%
echo "FIN: 9.3/4.1.9 %PGHOST%::%DB419%"
pause
rem exit /b
goto :EOF


:EOF
rem # /* EOF */
