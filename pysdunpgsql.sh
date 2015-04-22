#!/bin/bash



TODO подумать, чтоб сделать одну бд, для spectrdb и dfpostdb,
исключительно ради того, чтоб в одном месте была структура


export PGUSER=postgres
export PGPASSWORD=masterkey
#export PGOPTIONS='--client-min-messages=warning'
export PGHOST=127.0.0.1


sql_script=/home/ark/devel/nig/dfpost/xe3/trunk/DFLib/DataBase/dfPostDB\(IB\)/dfPostDB-pgsql.sql

dropdb pysdun
createdb pysdun

psql -h $PGHOST -U $PGUSER -d pysdun -f $sql_script


