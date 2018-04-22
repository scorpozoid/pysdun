#!/bin/bash

SRC_DB_NAME=dfpostdb
TEST_DB_NAME=dfpostdbpysdun
WORK_DIR=$HOME/devel/prj/pysdun
TS=`date +%Y.%m.%d` # `date +%Y.%m.%d.%H.%M.%S`
PGSQL_SCHEMA=${WORK_DIR}/${TS}-${SRC_DB_NAME}-pgsql.schema
MSSQL_SCHEMA=${WORK_DIR}/${TS}-${SRC_DB_NAME}-mssql.schema

export PGHOST=127.0.0.1
export PGHOSTADDR=127.0.0.1
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=masterkey
export PGCLIENTENCODING=UTF8

echo Dump scheme...
[ -f ${PGSQL_SCHEMA} ] || pg_dump -d ${SRC_DB_NAME} --schema=public --no-owner --no-privileges --schema-only -f ${PGSQL_SCHEMA}

tail ${PGSQL_SCHEMA} || exit

[ -x pgsql2mssql.py ] || chmod +x pgsql2mssql.py

[ -x pgsql2mssql.py ] && python pgsql2mssql.py -i ${PGSQL_SCHEMA} -o ${MSSQL_SCHEMA}

# TODO: use sqlcmd to create test database, https://docs.microsoft.com/en-us/sql/linux/quickstart-install-connect-ubuntu
# sqlcmd ... ${TEST_DB_NAME}
# sqlcmd -S localhost -U SA -P '<P@ssw0rd>'



# EOF

