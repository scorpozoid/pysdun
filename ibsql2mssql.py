#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This python script converts SQL-script written on Interbase/Firebird dialect
# to Microsoft SQLServer dialect
#
# 2015.05.14 [+] OOP style
#            [+] Python code style
#            [+] Triggers & stored procedures processing
# 2013.11.06 [+] Initial release, based on ibsql2mssql.py
#                for support serial autoincrement
#

import os
import sys
import getopt

from ibe_schema import IbeSchema
from pn_mssql import PysdunMssql


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
    pysdun = PysdunMssql(schema)
    pysdun.export(outfile)


if __name__ == "__main__":
    main(sys.argv[1:])
