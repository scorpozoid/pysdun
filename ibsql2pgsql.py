#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This python script converts SQL-script writeen on Interbase/Firebird dialect
# to PostgreSQL dialect
#
# 2013.11.06 [+] Initial release, based on ibsql2mssql.py
#                for support serial autoincrement
#
#
#


import sys, getopt
import re
import time
from datetime import date

from ddl import Field
from ddl import Table
from ddl import Descriptionary
from ddl import Generator

def debug(msg):
  # print(sys.stdout.encoding)
  print(msg.encode(sys.stdout.encoding, errors='replace'))


# rdt = replace data type
def rdt(datatype):

  re_autoinc = re.compile('(\w*)_autoinc', re.IGNORECASE)

  #for domain in domains:
  #  datatype = datatype.replace(domain, domains[domain])

  datatype = re.sub('character\s+set\s+\w+', '', datatype, flags=re.IGNORECASE)
  datatype = re.sub('collate\s+\w+', '', datatype, flags=re.IGNORECASE)
  if (datatype.lower().startswith('blob')):
    datatype = 'bytea'

  #datatype = datatype.replace('boolean', 'bit')
  #datatype = datatype.replace('default false', 'default 0')
  #datatype = datatype.replace('default true', 'default 1')
  datatype = datatype.replace('int64', 'numeric(18, 0)')
  datatype = datatype.replace('datetime', 'timestamp')


  #datatype = datatype.replace("value", fieldname) # for check constraints

  while -1 < datatype.find("  "):
    datatype = datatype.replace("  ", " ")
  while -1 < datatype.find(" )"):
    datatype = datatype.replace(" )", ")")


  datatype = re.sub('SUB\_TYPE\s+\d+', '', datatype, flags=re.IGNORECASE)
  datatype = datatype.replace('datetime', 'timestamp')
  #datatype = datatype.replace('numeric(18,0)', 'int64')
  #datatype = datatype.replace('numeric(18, 0)', 'int64')
  datatype = re.sub('DEFAULT\s+"NOW"', 'DEFAULT CURRENT_TIMESTAMP', datatype, flags=re.IGNORECASE)
  #datatype = re.sub('DEFAULT\s+"NOW"', 'DEFAULT GETDATE()', datatype, flags=re.IGNORECASE)
  #datatype = datatype.replace("default 'now'", 'datetime')
  datatype = datatype.replace("'NOW'", "CURRENT_TIMESTAMP")
  if (datatype.lower().startswith('blob')):
    datatype = 'bytea'
  #datatype = re.sub('character\s+set\s+\w+', '', datatype, flags=re.IGNORECASE)
  #datatype = re.sub('collate\s+\w+', '', datatype, flags=re.IGNORECASE)

  m = re_autoinc.search(datatype)
  if m is not None:
    domname = m.group(1)
    datatype += "default nextval('generator_" + domname + "')"

  if "GUID" in datatype:
    datatype = 'varchar(23)'
  return datatype


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
       infile = arg
    elif opt in ("-o", "--ofile"):
       outfile = arg
  # print('Input file is:' + infile)
  # print('Output file is:' + outfile)

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  try:
    #lines = [line.replace('\n', ' ') for line in open(infile)]
    #lines = [line.strip() for line in open(infile, encoding='utf-8')]
    lines = [line.strip() for line in open(infile)]
  except IOError as er:
    print('Can\'t open the "{0}" file'.format(er.infile))

  
  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  generators = {}

  re_gen = re.compile('CREATE\s+GENERATOR\s+(.*);', re.IGNORECASE)
  for statement in statements[:]:
    m = re_gen.search(statement);
    if m:
      gen_name = m.group(1).strip();
      gen = Generator(gen_name);
      generators[gen_name] = gen;

  re_genowner = re.compile('CREATE\s+TRIGGER\s+\w+\s+FOR\s+(\w+){.*}=\s+gen_id\((\w+),\s+\d+\).*;?', re.IGNORECASE)
  for statement in statements[:]:
    m = re_genowner.search(statement);
    if m:
      tabname = m.group(1).strip();
      genname = m.group(3).strip();
      print(tabname);
      print(genname);
      generators[genname].attab(tabname);
      generators.append(generator);

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  domains = {}
  redom = re.compile('CREATE\s+DOMAIN\s+(\w+)\s+AS\s+(.*);', re.IGNORECASE)
  for statement in statements[:]:
    m = redom.search(statement);
    if m:
      name = m.group(1)
      datatype = m.group(2).strip()
      datatype = rdt(datatype)
      domains[name] = datatype

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  descr = Descriptionary()
  for statement in statements[:]:
    m = re.match("describe\s+table\s+(\w+)\s+\'(.*)\'\;", statement, re.IGNORECASE | re.UNICODE)
    if m:
      descr.addtab(m.group(1), m.group(2))
      statements.remove(statement)
      continue
    m = re.match("describe\s+column\s+(\w+)\s+table\s+(\w+)\s+'(.*)'\;", statement, re.IGNORECASE | re.UNICODE)
    if m:
      descr.addfield(m.group(2), m.group(1), m.group(3))
      statements.remove(statement)
      continue

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  database = ""
  for statement in statements[:]:
    m = re.match("create database \'(.*)\' user.*password.*", statement, re.IGNORECASE)
    if m is not None:
      database = m.group(1)
      for item in ['.gdb', '.ib', '.fdb', "data/", "data\\", 'c:\\']:
        database = database.replace(item, '')
      statements.remove(statement)

  #for statement in statements:
  #  print(statement)
  #print('')

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  ins = []
  for statement in statements[:]:
    if statement.lower().startswith('insert'):
      #Этот код работает:
      #now = date.today().isoformat();
      #statement = statement.replace("'NOW'", "'" + now + "'");
      val = statement
      val = val.replace("'NOW'", "CURRENT_TIMESTAMP")
      val = val.replace("'now'", "CURRENT_TIMESTAMP")
      ins.append(val)
      statements.remove(statement)

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  viewlist = []
  for statement in statements[:]:
    m = re.match('create\s+view\s+(.*)\;', statement, re.IGNORECASE)
    if m is not None:
      viewlist.append(statement.rstrip(',').strip());
      statements.remove(statement)

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  schema = {}
  tablist = []

  for statement in statements:
    m = re.match('CREATE\s+TABLE\s+(\w+)\s+\((.*)\)\;', statement, re.IGNORECASE)
    if m is not None:
      tablename = m.group(1);
      table = Table(tablename, descr.table(tablename))
      fieldlist = map(lambda s: s.strip(' \t\n\r'), m.group(2).split(','))
      for fielditem in fieldlist:
        fm = re.match('(\w+)\s+(.*)', fielditem, re.IGNORECASE)
        if fm is not None:
          fieldname = fm.group(1)
          fieldtype = fm.group(2)

          fieldtype = rdt(fieldtype);

          null = False
          if "not null" in fieldtype:
            fieldtype = fieldtype.replace("not null", '')
            null = "not null"
          #debug(descr.field(tablename, fieldname))
          table.addf(fieldname, fieldtype, null, descr.field(tablename, fieldname))
      tablist.append(tablename)
      schema[tablename] = table
      continue

    m = re.match('alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+primary\s+key\s+\((.*)\)\;', statement, re.IGNORECASE)
    if m is not None:
      tablename = m.group(1)
      keyname = m.group(2)
      fieldlist = [item.strip() for item in m.group(3).split(',')]
      schema[tablename].addpk(keyname, list(fieldlist));
      continue

    #m = re.match('alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+foreign\s+key\s+\((.*)\)\s+references\s+(\w+)\s+\((\w+)\)\s?(on\s+delete\s+cascade)?\s?(on\s+update\s+cascade)?\s?(on\s+delete\s+no\s+action)?\s?(on\s+update\s+no\s+action)?.*\;', statement, re.IGNORECASE)
    m = re.match('alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+foreign\s+key\s+\((.*)\)\s+references\s+(\w+)\s+\((\w+)\)\s?(on\s+delete\s+cascade)?\s?(on\s+update\s+cascade)?.*\;', statement, re.IGNORECASE)
    if m is not None:
      tablename = m.group(1)
      keyname = m.group(2)
      fieldlist = [item.strip() for item in m.group(3).split(',')]
      reftab = m.group(4)
      reflist = [item.strip() for item in m.group(5).split(',')]
      del_rule = m.group(6)
      if del_rule is None:
        del_rule = "on delete no action"
      upd_rule = m.group(7)
      if upd_rule is None:
        upd_rule = "on update no action"
      schema[tablename].addfk(keyname, fieldlist, reftab, reflist, del_rule, upd_rule);
      continue

    m = re.match('alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+unique\s+\((.*)\)\;', statement, re.IGNORECASE)
    if m is not None:
      tablename = m.group(1)
      keyname = m.group(2)
      fieldlist = [item.strip() for item in m.group(3).split(',')]
      schema[tablename].adduk(keyname, fieldlist);
      continue

    m = re.match('create\s?(unique|asc|ascending|desc|descending)?\s+index\s+(\w+)\s+on\s+(\w+)\s+\((.*)\)\;', statement, re.IGNORECASE)
    if m is not None:
      tablename = m.group(3)
      xname = m.group(2)
      order = m.group(1)
      unique = None
      if order is not None:
        order = order.lower().strip();
        if order.startswith('asc'):
          order = "asc"
        elif order.startswith('desc'):
          order = "desc"
        elif order.startswith('uniq'):
          order = ""
          unique = "unique"
        else:
          order = "asc"
      else:
        order = "asc"
      fieldlist = [item.strip() for item in m.group(4).split(',')]
      schema[tablename].addx(xname, fieldlist, order, unique);
      continue
  # for statement in statements:

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  #for tablename in tablist:
  #  table = schema[tablename]
  #  print('')
  #  print(table.name + ' (' + table.descr + ')')
  #  for field in table.fields:
  #    print(field.name + ' ' + field.type)
  #  if table.pk is not None:
  #    print('pk: ' + ', '.join(str(x) for x in table.pk))
  #  if table.fk is not None:
  #    for key in table.fk:
  #      print('fk "' + key + '": ' + ', '.join(str(x) for x in table.fk[key]))
  #  if table.uk is not None:
  #    for key in table.uk:
  #      print('uk "' + key + '": ' + ', '.join(str(x) for x in table.uk[key]))
  #  if table.x is not None:
  #    for x in table.x:
  #      print('x "' + x + '": ' + ', '.join(str(x) for x in table.x[x]))
  #

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  ddl = []

  # 0.0) Create domains
  for domain_name in domains:
    domain_def = domains[domain_name]
    ddl.append('create domain {} as {}'.format(domain_name, domain_def))

  # 1.0) Create sequences
  for generator in generators:
    gen = generators[generator]
    ddl.append('create sequence {}'.format(gen.name))

  # id = []
  # 1.1) Create tables, primary keys, unique keys
  for tablename in tablist:
    table = schema[tablename]
    ddl.append('create table {} ({})'.format(
      tablename,
      #','.join([str(f.name + ' ' + f.type) for f in table.fields])
      ', '.join([str(f) for f in table.fields])
    ))
    #id.append('set identity_insert {} on'.format(tablename))

  # 1.2) Change sequences owners
  for generator in generators:
    gen = generators[generator]
    for tab in gen.tabs:
      ddl.append('alter sequence {} owned by {}'.format(gen.name, tab))

  # 2) Create primary keys, unique keys and indexes
  for tablename in tablist:
    table = schema[tablename]
    if table.uk is not None:
      for keyname in table.uk:
        fieldlist = table.uk[keyname];
        ddl.append('alter table {} add constraint {} unique ({})'.format(tablename, keyname, ', '.join([str(f) for f in fieldlist])))
    if table.x is not None:
      for xname in table.x:
        fieldlist = table.x[xname][0];
        order = table.x[xname][1];
        unique = table.x[xname][2];
        if order is None:
          order = ''
        if unique is None:
          unique = ''
        x = 'create {} index {} on {} ({})'.format(unique, xname, tablename, ', '.join([str(f + ' ' + order) for f in fieldlist]))
        x = x.replace('create  index', 'create index')
        ddl.append(x)
    if table.pk is not None:
      ddl.append('alter table {} add constraint pk_{} primary key ({})'.format(tablename, tablename, ', '.join([str(f) for f in table.pk])))

  # 3) Create foreign keys (references)
  for tablename in tablist:
    table = schema[tablename]
    if table.fk is not None:
      for fkname in table.fk:
        fieldlist = table.fk[fkname][0];
        reftab = table.fk[fkname][1];
        reflist = table.fk[fkname][2];
        del_rule = table.fk[fkname][3]
        if del_rule is None:
          del_rule = ""
        upd_rule = table.fk[fkname][4];
        if upd_rule is None:
          upd_rule = ""
        if del_rule:
          del_rule = del_rule.strip()
          # print('WARNING! NO ACTION! (' + fkname + ':' + del_rule + ')')
          # del_rule = "on delete no action"
        if upd_rule:
          upd_rule =  upd_rule.strip()
          # print('WARNING! NO ACTION! (' + fkname + ':' + upd_rule + ')')
          # upd_rule = "on update no action"
        alter = 'alter table {} add constraint {} foreign key ({}) references {} ({}) {} {}'.format(
          tablename, fkname, ', '.join([str(f) for f in fieldlist]),
          reftab, ', '.join([str(f) for f in reflist]), del_rule, upd_rule)
        # dfpost patch
        #alter = alter.replace('alter table navig', '-- alter table navig')
        #alter = alter.replace('alter table pf_result', '-- alter table pf_result')
        #alter = alter.replace('alter table worksession', '-- alter table worksession')
        ddl.append(alter)

  # print(php)
  f = open(outfile, 'w')
  try:
    for item in ddl:
      f.write(item + ';\n')
    for item in viewlist:
      f.write(item + ';\n')
    for item in ins:
      f.write(item + ';\n')
  finally:
    f.close()


  #for statement in statements:
  #  print(statement)
  #print('')



if __name__ == "__main__":
  main(sys.argv[1:])
