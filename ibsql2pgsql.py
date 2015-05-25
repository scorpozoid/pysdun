#!/usr/bin/env python
#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This python script converts SQL-script written on Interbase/Firebird dialect
# to PostgreSQL dialect
#
# 2015.04.21 [+] OOP style
#            [+] Python code style
#            [+] Triggers & stored procedures processing
# 2013.11.06 [+] Initial release, based on ibsql2pgsql.py
#                for support serial autoincrement
#
#
#
# if psql -lqt | cut -d \| -f 1 | grep -w <db_name>; then
#    # database exists
#    # $? is 0
# else
#    # ruh-roh
#    # $? is 1
# fi
#

#
# GUT!
#
# create or replace function trf_tr_abon_cdma_bi1_setnavig()
# returns trigger as
# $body$
#   declare LastNavig integer;
#   begin
#     select into LastNavig max(sys_id) from navig where navig.sysname = new.sysname;
#     new.navig_id = LastNavig;
#     return new;
#   end
# $body$
# language 'plpgsql'
# ;
#
# create trigger tr_abon_cdma_bi1_setnavig
# before insert
# on abon_cdma
# for each row execute procedure trf_tr_abon_cdma_bi1_setnavig()
# ;

import os
import sys
import getopt

from ibe_schema import IbeSchema
from pn_pgsql import PysdunPgsql


def debug(msg):
    # print(sys.stdout.encoding)
    print(msg.encode(sys.stdout.encoding, errors='replace'))


def main(argv):
    i = 0
    infile = ''
    outfile = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('ibsql2pgsql.py -i <infile> -o <outfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('ibsql2pgsql.py -i <infile> -o <outfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            infile = arg.strip()
        elif opt in ("-o", "--ofile"):
            outfile = arg.strip()
    print('Input file is:' + infile)
    print('Output file is:' + outfile)

    if not os.path.isfile(infile):
        print("Can't open file: '{}'".format(infile))
        exit()

    if '' == outfile:
        print("Can't create file w/o name: '{}'".format(outfile))
        exit()

    if os.path.isfile(outfile):
        os.remove(outfile)
    schema = IbeSchema(infile)
    # schema.print_schema()
    pysdun = PysdunPgsql(schema)
    pysdun.export(outfile)

    # try:
    #     lines = [line.strip() for line in open(outfile)]
    #     for line in lines:
    #         print(line)
    # except IOError as er:
    #     print("Can't open file: {0}".format(outfile))


if __name__ == "__main__":
    v_argv = (
        "-i",
        "C:/home/ark/devel/nig/dfpost/418/trunk/DFLib/DatabaseSrc/dfpostdb/ib/dfpostdb-ib.sql",
        "-o",
        "C:/home/ark/devel/nig/dfpost/418/trunk/DFLib/DatabaseSrc/dfpostdb/pgsql/dfpostdb-pgsql.sql"
    )
    main(v_argv)

    v_argv = (
        "-i",
        "C:/home/ark/devel/nig/dfpost/418/trunk/DFLib/DatabaseSrc/spectrdb/ib/spectrdb-ib.sql",
        "-o",
        "C:/home/ark/devel/nig/dfpost/418/trunk/DFLib/DatabaseSrc/spectrdb/pgsql/spectrdb-pgsql.sql"
    )
    main(v_argv)

    #main(sys.argv[1:])
