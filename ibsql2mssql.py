#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# 
# This python script converts SQL-script writeen on Interbase/Firebird dialect
# to Microsoft Transact-SQL compatible script
# 
# Restrictions: 
#   - Don't use comma (;) char anywthere except statement delimiter (for example, in object descriptions)
#   - Use simple english database object names (without spaces, national characters, etc)
#   - Dont't use remote server connection string (like 192.168.47.38:/srv/firebird/moonhattan) in source script 
#
# 2013.03.14 [+] Check for "describe column", "comment on" statements
# 2013.03.13 [+] Timestamp column datatype changed to datetime for MSSQL
#                GETDATE() used instead of "NOW" Firebird function
# 2013.01.01 [+] Initial release, base objects supported (database creation, domains, tables)
#                Not yet support for views, stored procedures and triggers
#                
# 
#


import sys, getopt
import re
import time
from datetime import date

def debug(msg):
  # print(sys.stdout.encoding)
  print(msg.encode(sys.stdout.encoding, errors='replace'))
  
# 
class Field:
  def __init__(self, name, type, null, descr):
    self.name = name
    self.type = type
    self.null = null
    self.descr = descr
  def __str__(self):
    if self.null:
      return "{} {} not null".format(self.name.strip(), self.type.strip())
    else:
      return "{} {}".format(self.name.strip(),  self.type.strip())
    
# 
class Table:
  def __init__(self, name, descr):
    self.name = name
    self.descr = descr
    self.fields = []
    self.pk = None
    self.fk = None
    self.uk = None
    self.x = None # indices (indexes)
    # debug('>' + name + ': ' + self.descr)
  def __str__(self):
    result = ''
    #for field in fields:
    #  result += field.name + ' '
    return self.name + result
  def addf(self, fieldname, type, null, descr):
    self.fields.append(Field(fieldname, type, null, descr))
  def addpk(self, keyname, fieldlist):
    self.pk = fieldlist
  def addfk(self, keyname, fieldlist, reftab, reflist, delrule, updrule):
    if self.fk is None:
      self.fk = {}
    self.fk[keyname] = [fieldlist, reftab, reflist, delrule, updrule]
  def adduk(self, keyname, fieldlist):
    if self.uk is None:
      self.uk = {}
    self.uk[keyname] = fieldlist
  def addx(self, xname, fieldlist, order, unique):
    if self.x is None:
      self.x = {}
    self.x[xname] = [fieldlist, order, unique]
    
# 
class Descriptionary:    
  def __init__(self):
    self.descr = {}
  def addtab(self, tab, descr):
    self.descr[tab] = descr
    #debug(tab + ': ' +descr)
  def addfield(self, tab, field, descr):
    key = tab + '-' + field
    self.descr[key] = descr
    #debug(key + ': ' + descr)
  def table(self, tab):
    if self.descr.get(tab) is not None:
      #debug(tab + ': ' + self.descr[tab])
      return self.descr[tab]
    else:
      return ''
  def field(self, tab, field):
    key = tab + '-' + field
    if self.descr.get(key) is not None:
      #debug(key + ': ' + self.descr[key])
      return self.descr[key]
    else:
      return ''
      
def main(argv):
  i = 0
  infile = ''
  outfile = ''
  try:
    opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
  except getopt.GetoptError:
    print('ibsql2mssql.py -i <infile> -o <outfile>')
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
       print('ibsql2mssql.py -i <infile> -o <outfile>')
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

  setterm = re.compile('SET\s+TERM\s+?([\;\^])\s+?([\;\^])', re.IGNORECASE)
  term = ';'
  buf = ''
  statements = []
  comment = False
  i = 0;
  for line in lines:
    m = setterm.search(line)
    if m is not None:
      term = m.group(1)
    x = line.find('--')
    if (-1 < x):
      line = line[:x]
    x1 = line.find('/*')
    x2 = line.find('*/')
    if (-1 < x1) or (-1 < x2):
      if (-1 < x1) and (-1 < x2):
        line = line[:x1] + line[x2 + 2:]
      else:
        if -1 < x1:
          line = line[:x1]
          comment = True
        else:
          line = line[x2 + 2:]
          comment = False

    if ('' == line) or comment:
      continue
    buf = buf + line + ' ';
    if (term in buf.lower()):
      if setterm.match(buf) is None:
        buf = re.sub('[\ +\t+\r+\n+]', ' ', buf).strip()
        buf = buf.replace('( ', '(')
        if buf.lower().startswith('insert'):
          statements.append(buf)
        else:
          statements.append(buf.lower());
      buf = ''
  #for statement in statements:
  #  print(statement)
  #print('')

  # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
  domains = {}
  redom = re.compile('CREATE\s+DOMAIN\s+(\w+)\s+AS\s+(.*);', re.IGNORECASE)
  for statement in statements[:]:
    m = redom.search(statement);
    if m:
      datatype = m.group(2).strip()
      domain = m.group(1);
      datatype = re.sub('SUB\_TYPE\s+\d+', '', datatype, flags=re.IGNORECASE)
      # Тип данных timestamp - это синоним к типу данных rowversion и не предназначен для хранения даты и времени
      # поэтому недо заменить его на datetime (или datetime2), тем более что
      # GETDATE() в MSSQL работает только с полями типа datetime, с timestamp-полями - не работает
      # datatype = re.sub('DEFAULT\s+"NOW"', '', datatype)
      datatype = datatype.replace('timestamp', 'datetime')
      datatype = datatype.replace('numeric(18,0)', 'int64')
      datatype = datatype.replace('numeric(18, 0)', 'int64')
      datatype = re.sub('DEFAULT\s+"NOW"', 'DEFAULT GETDATE()', datatype, flags=re.IGNORECASE)
      if (datatype.lower().startswith('blob')):
        datatype = 'varbinary(max)'
        # datatype = 'binary'
      datatype = re.sub('character\s+set\s+\w+', '', datatype, flags=re.IGNORECASE)
      datatype = re.sub('collate\s+\w+', '', datatype, flags=re.IGNORECASE)
     
      if "_autoinc" in domain:
        #print(domain)
        #datatype = datatype + 'identity (1, 1)'
        datatype = datatype + ' identity'
      
      if "GUID" in domain:
        datatype = 'varchar(23)'
        
      domains[domain] = datatype
      statements.remove(statement)
  #for i in range(len(statements)):
  #  for domain in domains:
  #    statements[i] = statements[i].replace(domain, domains[domain])
      #print(statement)
  #for statement in statements:
  #  print(statement)
  #print('')
      
  #print(domains)
      
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
      val = val.replace("'NOW'", "getdate()")
      val = val.replace("'now'", "getdate()")
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

          for domain in domains:
            fieldtype = fieldtype.replace(domain, domains[domain])
          
          fieldtype = re.sub('character\s+set\s+\w+', '', fieldtype, flags=re.IGNORECASE)
          fieldtype = re.sub('collate\s+\w+', '', fieldtype, flags=re.IGNORECASE)
          if (fieldtype.lower().startswith('blob')):
            fieldtype = 'varbinary(max)'
          
          fieldtype = fieldtype.replace('boolean', 'bit')
          fieldtype = fieldtype.replace('default false', 'default 0')
          fieldtype = fieldtype.replace('default true', 'default 1')
          fieldtype = fieldtype.replace('int64', 'numeric(18,0)')
          fieldtype = fieldtype.replace('identity', 'identity (1,1)')
          fieldtype = fieldtype.replace('timestamp', 'datetime')

          #fieldtype = re.sub('DEFAULT\s+"NOW"', 'DEFAULT GETDATE()', fieldtype, flags=re.IGNORECASE)
          #fieldtype = fieldtype.replace("default 'now'", 'datetime')
          fieldtype = fieldtype.replace("'NOW'", "getdate()")
          
          fieldtype = fieldtype.replace("value", fieldname) # for check constraints

          while -1 < fieldtype.find("  "):
            fieldtype = fieldtype.replace("  ", " ")
          while -1 < fieldtype.find(" )"):
            fieldtype = fieldtype.replace(" )", ")")
           
          
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
  cdb = [] # create database ...
  datapath = "C:\\Program Files\\Microsoft SQL Server\\MSSQL11.MSSQLSERVER\\MSSQL\\DATA"

  #  
  # use [master]
  # go
  # declare @datapath varchar(max) = '';
  # select @datapath = substring(physical_name, 1, charindex(N'master.mdf', lower(physical_name)) - 1)
  # from master.sys.master_files
  # where database_id = 1 and file_id = 1
  # print @datapath
  # go
  #  
  
  cdb.append("use [master]")
  # cdb.append("if exists(select * from sys.databases where name = '{0}') drop database {0}".format(database))
  cdb.append("if exists(select * from sys.databases where name = '{0}')".format(database))
  cdb.append("begin");
  cdb.append("  print 'Database {0} exists'".format(database));
  cdb.append("  alter database {0} set offline with rollback immediate".format(database));
  #cdb.append("  go");
  cdb.append("  alter database {0} set online".format(database));
  #cdb.append("  go");
  cdb.append("  drop database {0}".format(database));
  #cdb.append("  go");
  cdb.append("end");
  cdb.append("else");
  cdb.append("begin");
  cdb.append("  print 'Database {0} does not exists'".format(database));
  cdb.append("end");
  
  cdb.append("create database [{0}]".format(database, datapath))
  cdb.append("go");

  cdb.append("alter database [{0}] collate Cyrillic_General_CI_AS".format(database))
  cdb.append("go");
  
  cdb.append("use [{0}]".format(database))

  ddl = []
  #id = []
  # 1) Create tables, primary keys, unique keys
  for tablename in tablist:
    table = schema[tablename]
    ddl.append('create table {} ({})'.format(
      tablename, 
      #','.join([str(f.name + ' ' + f.type) for f in table.fields])
      ', '.join([str(f) for f in table.fields])
    ))
    
    #id.append('set identity_insert {} on'.format(tablename))

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
    for item in cdb:
      f.write(item + '\n')
    f.write('\ngo\n\n')
    for item in ddl:
      f.write(item + '\n')
    f.write('\ngo\n\n')
    for item in viewlist:
      f.write(item + '\ngo\n')
    #for item in id:
    #  f.write(item + '\n')
    for item in ins:
      f.write(item + '\n')
    f.write('\ngo\n\n')
  finally:
    f.close()
  
  
  #for statement in statements:
  #  print(statement)
  #print('')
  
  
  
if __name__ == "__main__":
  main(sys.argv[1:])
