#!/bin/bash
#
#
# TODO подумать, чтоб сделать одну бд, для spectrdb и dfpostdb, исключительно ради того, чтоб в одном месте была структура
#
# TODO: dvbservice -> dvbservice_gen - rename
# TODO: offset - rename
# TODO: interval - rename
# TODO: проверить нужно ли в триггерах делать for each row, а не for each statement
#

export PGUSER=postgres
export PGPASSWORD=masterkey
#export PGOPTIONS='--client-min-messages=warning'
export PGHOST=127.0.0.1

PROJROOT=/home/ark/devel/nig/dfpost/418/trunk

TESTDB=pysdun


sqli=$PROJROOT/DFLib/DataBase/dfPostDB\(IB\)/dfPostDB.sql
sqlo=$PROJROOT/DFLib/DataBase/dfPostDB\(PGS\)/dfPostDB.sql

python ibsql2pgsql.py -i $sqli -o $sqlo

dropdb $TESTDB
createdb $TESTDB

psql -h $PGHOST -U $PGUSER -d $TESTDB -f $sqlo

sqlot=$PROJROOT/DFLib/DataBase/dfPostDB\(PGS\)/dfPostDB-triggers.sql

psql -h $PGHOST -U $PGUSER -d $TESTDB -f $sqlot


