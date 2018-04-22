#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This python script converts PostgreSQL dump
# to Microsoft SQLServer T-SQL script
#
# 2018.03.29 [+] initial (oop style)
#

import os
import sys
import getopt

from pg_schema import PgSchema
from pn_mssql import PysdunMssql


def debug(msg):
    # print(sys.stdout.encoding)
    print(msg.encode(sys.stdout.encoding, errors='replace'))


def main(argv):
    i = 0
    infile = ''
    outfile = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["infile=", "outfile="])
    except getopt.GetoptError:
        print('pgsql2mssql.py -i <infile> -o <outfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('pgsql2mssql.py -i <infile> -o <outfile>')
            sys.exit()
        elif opt in ("-i", "--infile"):
            infile = arg.strip()
        elif opt in ("-o", "--outfile"):
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
    schema = PgSchema(infile)
    # schema.print_schema()
    pysdun = PysdunMssql(schema)
    pysdun.export(outfile)


if __name__ == "__main__":
    main(sys.argv[1:])
