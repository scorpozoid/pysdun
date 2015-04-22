@echo off

set HOME=C:\home\ark
set PATH=%PATH%;%HOME%\bin\python-2.7.6.1\App
set PATH=%PATH%;%HOME%\bin\python-3.2.1.1\App
set PATH=%PATH%;%HOME%\devel\shell\devel
rem set IBESCRIPT=%HOME%\devel\nig\dfpost\418\trunk\DFLib\DataBase\dfPostDB(IB)\dfPostDB.sql
rem python %HOME%\devel\shell\devel\db\ibsql2mssql.py -i %IBESCRIPT% -o %IBESCRIPT%-pg.sql
python ibsql2pgsql-temp.py
pause
