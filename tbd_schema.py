#!/usr/bin/python
# -*- coding: utf-8 -*- 

#

import sys
import re
import codecs
import os
import getopt

from os import path

import ibe_ddl
from ibe_ddl import Schema
from ibe_ddl import Domain
from ibe_ddl import Table

def debug(msg):
    print(msg.encode(sys.stdout.encoding, errors='replace'))


class TdbIndieSchema(Schema):

    def __init__(self, filename):
        Schema.__init__(self)
        self.__base_types = {}
        self.__tab_names = {}
        self.__lines = []
        self.load(filename);
        
        
    def load(self, filename):
        try:
            file = codecs.open(filename, encoding='utf-8')
            self.__lines = file.readlines()

            self.predefine_domains()
            self.collect_base_types()
            self.process_blocks()

        except IOError as er:
            print('Can\'t open the "{0}" file'.format(filename))
              
            
    def get_field_type(self, value):
        cLinkType = u'Ссылка'.lower()
        cFileType = u'Файл'.lower()
        cTextType = u'Символьное'.lower()
        cStringType = u'Строка'.lower()
        cFloatType = u'Численное'.lower()
        cNumericType = u'Числовое'.lower()
        cIntType = u'Целое'.lower()
        cTimestampType = u'Дата, время'.lower().replace(' ', '')
        cDateType = u'Дата'.lower()
        cTimeType = u'Время'.lower()
        cReferenceType = u'БД'.lower()
        cGeoType = u'Град. мин. сек'.lower().replace(' ', '')

        if cTextType == value or cStringType == value:
            return 'text_t'
        elif cIntType == value:
            return 'int_t'
        elif cFloatType == value or cNumericType == value:
            return 'double_t'
        elif cTimeType == value:
            return 'time_t'
        elif cDateType == value:
            return 'date_t'
        elif cTimestampType == value:
            return 'timestamp_t'
        elif value.startswith(cFileType):
            return 'file_t'
        elif cLinkType == value:
            return 'filename_t'
        elif cGeoType == value:
            return 'lla_t'
        elif cReferenceType == value:
            return '<REF>'
        else:
            return ''
      
      
    def predefine_domains(self):
        self.domains.append(Domain('text_t', 'varchar(1024)', False))
        self.domains.append(Domain('int_t', 'integer', False))
        self.domains.append(Domain('double_t', 'double precision', False))
        self.domains.append(Domain('timestamp_t', 'timestamp', False))
        self.domains.append(Domain('time_t', 'time', False))
        self.domains.append(Domain('date_t', 'date', False))
        self.domains.append(Domain('lla_t', 'varchar(128)', False))
        self.domains.append(Domain('file_t', 'blob', False))
        self.domains.append(Domain('filename_t', 'varchar(1024)', False))


    def collect_base_types(self):
      block = []
      cur_tab_name = ''
      cur_tab_no = ''
      pre_tab_no = 0
      for lineitem in self.__lines:
          line = lineitem.strip().rstrip('\r').rstrip('\n')
          print(line)
          if line == "":
            
              if 1 == len(block):
                  if not block[0].isdigit():
                      print ('NONDIGIT "' + block[0] + '"')
                      block = []
                      
              if 3 == len(block):
                  cur_tab_no = block[0]
                  cur_tab_name = block[2].lower().replace(' ', '_').replace('\t', '_')
                  
                  print('T' + cur_tab_no + ' ' + cur_tab_name)
                  if (cur_tab_name.startswith('(')) and (cur_tab_name.endswith(')')):
                      cur_tab_name = cur_tab_name[1:-1]
                  self.__tab_names[int(cur_tab_no)] = cur_tab_name
                  if int(cur_tab_no) == int(pre_tab_no + 1):
                      pre_tab_no = int(cur_tab_no)
                  else:
                    print(u'TABLE ORDERING MISMATCH ' + cur_tab_no + ' ' + str(pre_tab_no))
                  block = []
                  
              elif 3 < len(block):
                field_name = block[2].lower().replace(' ', '_').replace('\t', '_')
                field_type = block[3].lower().replace(' ', '').replace('\t', '')
                
                field_type = self.get_field_type(field_type)
                
                if '<REF>' == field_type:
                  field_type = ''
              
                if '' <> field_type:
                  reftype_key = cur_tab_name + '::' + field_name
                  self.__base_types[reftype_key] = field_type
                  print('> ' + reftype_key + ' -> ' + field_type)
                
                block = []
          else:  
              block.append(line)


    def process_blocks(self): 

        block = []
        cur_tab_name = ''
        table = None;
        
        for lineitem in self.__lines:
            
            line = lineitem.strip().rstrip('\r').rstrip('\n')
            
            if line == "":
              
                if 1 == len(block):
                    if not block[0].isdigit():
                      block = []
                      
                if 3 == len(block):
                    if not table is None:
                        self.tables[cur_tab_name] = table
                    tab_no = block[0]
                    tab_caption = block[1]
                    tab_name = block[2].lower().replace(' ', '_').replace('\t', '_')
                    if (tab_name.startswith('(')) and (tab_name.endswith(')')):
                        tab_name = tab_name[1:-1]
                    table = Table(tab_name, tab_caption + ' [' + tab_no + ']');
                    cur_tab_name = tab_name
                    block = []
                    
                elif 3 < len(block):
                    field_num = block[0]
                    field_caption = block[1]
                    field_name = block[2].lower().replace(' ', '_').replace('\t', '_')
                    field_len = 0
                    field_ref = ''
                    field_type = block[3].lower().replace(' ', '').replace('\t', '')
                    field_type = self.get_field_type(field_type)

                    # print('T' + tab_no + ' ' + cur_tab_name + '  ' + field_name + ' ' + field_type)

                    ref_tab_name = '<TABLE>'
                    ref_field_name = field_name

                    if '<REF>' == field_type:
                        table_ref = ''
                        if 'ID_Histor'.lower() == field_name and 6 > len(block):
                          table_ref = u'БД № 6'
                        if table_ref == '':
                          if 5 < len(block):
                              table_ref = block[5]
                          else:
                              table_ref = ''
                              print('== WRONG LINE COUNT ' + str(len(block)) + '==' + cur_tab_name + '======')
                              for b in block:
                                  print(b)
                              print('========')
                            
                        if table_ref <> '':
                            table_ref = table_ref.replace(u'№', '').replace(u'БД', '').replace(u'DBNO', '').strip();
                            if table_ref.isdigit():
                                ref_tab_no = table_ref;
                                ref_tab_name = self.__tab_names[int(ref_tab_no)]
                                base_type_key = ref_tab_name + '::' + ref_field_name
                                if base_type_key in self.__base_types:
                                    field_type = self.__base_types[base_type_key]
                                else:
                                    print('NO REFERENCE FOR "' + base_type_key + '"')
                                    field_type = 'int_t'
                            else:
                                print('WRONG REFERENCE NO "' + table_ref + '"')
                                field_type = 'int_t'
                    
                    if field_type == '':
                        field_type = block[3].strip().lower()
                    
                    table.add_field(field_name, field_type, False, field_caption)
                    
                    if '<REF>' == field_type:
                        fk_key_name = 'fk_' + cur_tab_name + '_' + field_name + '_' + ref_tab_name + '_' + ref_field_name
                        field_list = [field_name]
                        ref_field_list = [field_name]
                        table.add_fk(fk_key_name, field_list, ref_tab_name, ref_field_list, 'cascade', 'cascade')
                      
                    block = []
            else:  
                block.append(line)
              
        print('\n' * 3)

        for t in self.tables:
            print(t)
            for f in table.fields:
                print('  ' + f.name + '  ' + f.data_type)
          


