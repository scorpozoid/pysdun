
TODO: взять отсюда все полезное и перенести в pn_drupal2oop.py и удалить

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# ibsql2ds converts interbase DDL script (sql) to Drupal schema (php) converter
#
# Usage: ibsql2ds -i <infile.sql> -o <outfile.drupalschema>
#
# This python script converts SQL-script writeen on Interbase/Firebird dialect
# (usually generated with IBExpert) to Drupal module schema script
#
# Restrictions:
#  - Don't use comma (;) char anywthere except statement delimiter (for example, in object descriptions)
#  - Use simple english database object names (without spaces, national characters, etc)
#  - Dont't use remote server connection string (like 192.168.47.38:/srv/firebird/moonhattan) in source script
#
# 2013.06.15 [+] Initial script
#
#
#

import sys, getopt
import re
import time
from datetime import date

descrdic = {}

def fieldkey(tab, field):
  return tab + '-' + field

def descr(key):
  if descrdic.get(key) is None:
    return ''
  return descrdic[key]

def main(argv):
  i = 0
  infile = ''
  outfile = ''
  try:
    opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
  except getopt.GetoptError:
    print('ibsql2ds-1.py -i <infile> -o <outfile>')
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
       print('ibsql2ds-1.py -i <infile> -o <outfile>')
       sys.exit()
    elif opt in ("-i", "--ifile"):
       infile = arg
    elif opt in ("-o", "--ofile"):
       outfile = arg
  # print('Input file is:' + infile)
  # print('Output file is:' + outfile)

  try:
    # win lines = [line.replace('\n', ' ') for line in open(infile, encoding='utf-8')]
    lines = [line.replace('\n', ' ') for line in open(infile)]
  except IOError as er:
    print('Can\'t open the "{0}" file'.format(er.infile))
  all = ''.join(lines)
  domains = {}
  ptndom = 'CREATE\s+DOMAIN\s+(\w+)\s+AS\s+([\w\ \(\d\)"]+)\;';
  # print(ptndom)
  redom = re.compile(ptndom, re.IGNORECASE)
  for match in redom.finditer(all):
    datatype = match.group(2).strip()
    datatype = re.sub('SUB\_TYPE\s+\d+', '', datatype)
    # В Drupal 7 уже нет поля типа дата\время, используем для него int (unix time)
    datatype = datatype.replace('TIMESTAMP', 'int')
    datatype = datatype.replace('TIME', 'int')
    datatype = datatype.replace('DATETIME', 'int')
    datatype = datatype.replace('DATE', 'int')
    datatype = re.sub('DEFAULT\s+"NOW"', '', datatype)
    if (datatype.lower().startswith('blob')):
      datatype = 'blob' # 'text'
    domains[match.group(1).lower()] = datatype.lower()

  #print(domains)

  ptnterm = 'SET\s+TERM\s+(\w)\s+(\w)';
  reterm = re.compile(ptnterm, re.IGNORECASE)
  term = ';'
  buf = ''
  statements = []
  comment = False
  for line in lines:
    m = reterm.search(line)
    if m is not None:
      term = m.group(2)
    x = line.find('--');
    if (-1 < x):
      line = line[:x]
    x1 = line.find('/*');
    x2 = line.find('*/');
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

    buf = buf + line
    if 0 < line.find(term):
      buf = buf.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ').strip()
      statements.append(buf)
      buf = ''
  #print(statements)

  ddl = []
  for statement in statements:
    if (
        (not statement.lower().startswith('DESCRIBE')) and
        (not statement.lower().startswith('create table')) and
        (not statement.lower().startswith('create index')) and
        (not
          ('alter table') and (
            ('unique' in statement.lower()) and
            ('foreign key' in statement.lower()) and
            ('primary key' in statement.lower())
          )
        )
       ):
        continue;
    for domain in domains:
      statement = statement.lower().replace(domain, domains[domain])
    ddl.append(statement)

  #print (ddl)

  schema = {}
  crtab_pattern = 'CREATE\s+TABLE\s+(\w+)\s+\((.*)\)\;';
  crtab_regexp = re.compile(crtab_pattern, re.IGNORECASE)

  field_pattern = '(\w+)\s+(.*)';
  firld_regexp = re.compile(field_pattern, re.IGNORECASE)

  pk_pattern = 'alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+primary\s+key\s+\((.*)\)\;';
  pk_regexp = re.compile(pk_pattern, re.IGNORECASE)

  uk_pattern = 'alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+unique\s+\((.*)\)\;';
  uk_regexp = re.compile(uk_pattern, re.IGNORECASE)

  fk_pattern = 'alter\s+table\s+(\w+)\s+add\s+constraint\s+(\w+)\s+foreign\s+key\s+\((.*)\)\s+references\s+(\w+)\s+\((\w+)\).*\;';
  fk_regexp = re.compile(fk_pattern, re.IGNORECASE)

  x_pattern = 'create\s?(asc|ascending|desc|descending)?\s+index\s+(\w+)\s+on\s+(\w+)\s+\((.*)\)\;';
  x_regexp = re.compile(x_pattern, re.IGNORECASE)


  for ddlitem in ddl:
    tabmatch = crtab_regexp.search(ddlitem)
    if tabmatch is not None:
      table = {}
      tab = tabmatch.group(1)
      if 'drupal_users' == tab:
        continue;
      fieldlist = tabmatch.group(2).split(',')
      fieldlist = map(lambda s: s.strip(' \t\n\r'), fieldlist)
      fields = {}
      for fielditem in fieldlist:
        fieldmatch = firld_regexp.search(fielditem)
        if fieldmatch is not None:
          fieldname = fieldmatch.group(1)
          fieldtype = fieldmatch.group(2)
          fields[fieldname] = fieldtype
      table['fields'] = fields
      schema[tab] = table

    pk_match = pk_regexp.search(ddlitem)
    if pk_match is not None:
      tab = pk_match.group(1)
      pk_fields = pk_match.group(3).split(',')
      pk_fields = ["'{}'".format(item.strip()) for item in pk_fields]
      pk_field = ', '.join(pk_fields);
      schema[tab]['pk'] = "array({})".format(pk_field)

    fk_match = fk_regexp.search(ddlitem)
    if fk_match is not None:
      tab = fk_match.group(1)
      fk_name = fk_match.group(2)
      fk_field = fk_match.group(3)
      ref_tab = fk_match.group(4)
      ref_field = fk_match.group(5)
      if schema[tab].get('fk') is None:
        schema[tab]['fk'] = {}
      schema[tab]['fk'][fk_name] = "\n\
          '{}' => array(\n\
           array(\n\
             'table' => '{}',\n\
             'columns' => array('{}' => '{}')\n\
           ),\n\
          ),\n".format(fk_name, ref_tab, fk_field, ref_field)

    uk_match = uk_regexp.search(ddlitem)
    if uk_match is not None:
      tab = uk_match.group(1)
      uk_name = uk_match.group(2)
      uk_fields = uk_match.group(3).split(',')
      uk_fields = ["'{}'".format(item.strip()) for item in uk_fields]
      uk_field = ', '.join(uk_fields);
      if schema[tab].get('uk') is None:
        schema[tab]['uk'] = {}
      schema[tab]['uk'][uk_name] = "\n\
          '{}' => array({}),\n".format(uk_name, uk_field)

    x_match = x_regexp.search(ddlitem)
    if x_match is not None:
      x_order = x_match.group(1)
      if x_order is not None:
        if statement.lower().startswith('asc'):
          x_order = "asc"
        else:
          x_order = "desc"
      else:
        x_order = "asc"
      x_name = x_match.group(2)
      tab = x_match.group(3)
      x_fields = x_match.group(4).split(',')
      x_fields = ["'{}'".format(item.strip()) for item in x_fields]
      x_field = ', '.join(x_fields);
      if schema[tab].get('x') is None:
        schema[tab]['x'] = {}
      schema[tab]['x'][x_name] = "\n\
          '{}' => array({}),\n".format(x_name, x_field)


    if ddlitem.lower().startswith('describe'):
      # АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩ абвгдежзиклмнопрстуфхцчшщ
      # match = re.match("describe\s+table\s+(\w+)\s+\'([ a-zA-ZА-Я0-9]+)\'\;".encode('utf-8'), ddlitem, re.IGNORECASE | re.UNICODE)
      match = re.match("describe\s+table\s+(\w+)\s+\'(.*)\'\;", ddlitem, re.IGNORECASE | re.UNICODE)
      if match:
        t = match.group(1)
        n = match.group(2)
        descrdic[t] = n

      match = re.match("describe\s+column\s+(\w+)\s+table\s+(\w+)\s+'(.*)'\;", ddlitem, re.IGNORECASE)
      if match:
        t = match.group(2)
        f = match.group(1)
        n = match.group(3)
        descrdic[fieldkey(t, f)] = n

  #print descrdic;

  #print schema

  php = []

  #php.append("<?php\n\
  php.append("\
    /**\n\
     * Implementation of hook_schema().\n\
     */\n\
    function rsv_schema() {\n")

  ptnvchar = '(var)?char\((\d+)\)';
  revchar = re.compile(ptnvchar, re.IGNORECASE)
  for tab in schema:
    php.append("\
      $schema['rsv_{}'] = array(\n\
        'description' => t('{}'),\n\
        'fields' => array(\n"
      .format(tab, descr(tab)))
    for field in schema[tab]['fields']:
      nullable = ""
      flen = ""
      default = "'default' => {},".format(0)
      ftype = schema[tab]['fields'][field]
      if ("not null" in ftype.lower()):
        nullable = "'not null' => TRUE,"
      m = revchar.search(ftype)
      if m is not None:
        l = int(m.group(2));
        # 1000 bytes is limit for key fields for mysql
        # When using utf-8 (2 byte for char) use text insted varchar
        if (1000 / 2) > l:
          ftype = "varchar"
          default = "''"
          flen = "'length' => '{}',".format(l)
          default = "'default' => {},".format("''")
        else:
          ftype = "text"
          default = ""
      else:
        ftype = ftype.replace('double precision', 'float')
        ftype = ftype.replace('datetime', 'int')
        ftype = ftype.replace('integer not null', 'int')
        ftype = ftype.replace('integer', 'int')

      php.append("\n\
          '{}' => array(\n\
            'description' => t('{}'),\n\
            'type' => '{}',\n\
            {}\n\
            {}\n\
            {}\n\
          ),\n"
        .format(field, descr(tab + '-' + field), ftype, flen, nullable, default))
    php.append("\n\
        ),"); # fields

    if 'pk' in schema[tab]:
      pk = schema[tab]['pk']
      php.append("\n\
        'primary key' => {},".format(pk)
      )
    else:
      php.append("\
        // <!-- no pk -->")

    if 'fk' in schema[tab]:
      php.append("\n\
        'foreign keys' => array(\n")
      for fk_name in schema[tab]['fk']:
        php.append(schema[tab]['fk'][fk_name])
      php.append("\n\
        ),\n");
    else:
      php.append("\
        // <!-- no fk -->")


    if 'uk' in schema[tab]:
      php.append("\n\
        'unique keys' => array(\n")
      for uk_name in schema[tab]['uk']:
        php.append(schema[tab]['uk'][uk_name])
      php.append("\n\
        ),\n");
    else:
      php.append("\
        // <!-- no uk -->")

    if not 'x' in schema[tab]:
      php.append("\
        // <!-- no indices -->")
    else:
      php.append("\
        'indexes' => array(");
      for x_name in schema[tab]['x']:
        php.append(schema[tab]['x'][x_name])
      php.append("\n\
        )");
    php.append("\n\
      );")
  php.append("\n\
      return $schema;\n\
    }") # function conso_schema


  # print(php)
  f = open(outfile, 'w')
  try:
    for item in php:
      f.write(item + '\n')
      i = i + 1
  finally:
    f.close()

  # remove empty lines
  php = list(line for line in (l.rstrip() for l in open(outfile)) if line)

  ident = 4
  f = open(outfile, 'w')
  try:
    for item in php:
      if ident < len(item):
        if '' == item[:ident].strip():
          item = item[ident:]
      f.write(item + '\n')
  finally:
    f.close()

  print("OK ({})".format(i))

if __name__ == "__main__":
  main(sys.argv[1:])
