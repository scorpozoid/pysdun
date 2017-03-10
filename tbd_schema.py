#!/usr/bin/python
# -*- coding: utf-8 -*- 

#

#
# 
#
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
        self.__current_table = None
        self.__current_table_code = ''
        self.__base_types = {}
        self.__tab_names = {}
        self.__uk_keys = {}
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
              
            
    def strip_line(self, line):
        #line = line.replace(u'«История»', u'История')
        line = line.replace(u'…', '...')
        line = line.replace('....', '...')
        line = line.replace('... .', '...')
        line = line.replace(u'«', "[")
        line = line.replace(u'»', "]")
        line = line.strip().rstrip('\r').rstrip('\n')
        return line
            
    def get_associated_domain(self, value):
        #debug('GFT ' + value)
        
        cLinkType = u'Ссылка'.lower()
        cFileType = u'Файл'.lower()
        cTextType = u'Символьное'.lower()
        cMemoTypeRu = u'М'.lower()
        cMemoTypeEn = u'M'.lower()
        cStringTypeRu = u'Строка'.lower()
        cStringTypeCharRu = u'С'.lower()
        cStringTypeCharEn = u'C'.lower()
        cNumericType1 = u'Числовое'.lower()
        cNumericType2 = u'Численное'.lower()
        cNumericType3 = u'N'.lower()
        cIntType = u'Целое'.lower()
        cTimestampType1 = u'Дата, время'.lower().replace(' ', '')
        cTimestampType2 = u'Время, Дата,'.lower().replace(' ', '') 
        cTimestampType3 = u'Время, Дата'.lower().replace(' ', '') 
        cDateType = u'Дата'.lower()
        cDateTypeChar = u'D'.lower()
        cTimeType = u'Время'.lower()
        cReferenceType1 = u'БД'.lower()
        cReferenceType2 = u'@@DBT'.lower()
        cGeoType = u'Град. мин. сек'.lower().replace(' ', '')

        value = value.lower().replace(' ', '').replace('\t', '')

        if value in (cTextType, cStringTypeRu, cStringTypeCharRu, cStringTypeCharEn, cMemoTypeRu, cMemoTypeEn):
            return 'text_t'
        elif cIntType == value:
            return 'int_t'
        elif value in (cNumericType1, cNumericType2, cNumericType3):
            return 'double_t'
        elif cTimeType == value:
            return 'time_t'
        elif value in (cDateTypeChar, cDateType):
            return 'date_t'
        elif value in (cTimestampType1, cTimestampType2, cTimestampType3):
            return 'timestamp_t'
        elif value.startswith(cFileType):
            return 'file_t'
        elif cLinkType == value:
            return 'filename_t'
        elif cGeoType == value:
            return 'lla_t'
        elif 'user_id_t' == value:
            return 'user_id_t'
        elif 'database_id_t' == value:
            return 'database_id_t'
        elif value.startswith(cReferenceType1) or value.startswith(cReferenceType2):
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
        self.domains.append(Domain('user_id_t', 'text', False))
        self.domains.append(Domain('database_id_t', 'text', False))


    def get_dbt_code(self, value):

        #print('get_dbt_code("' + value + '")')
        #num = float(value)
        #i, f = divmod(num, 1)
        #return str(int(i * 100 + f * 10)).zfill(5)

        #m = re.match('(\d+)\.?(\d+)', value, re.IGNORECASE)
        #if m:
        #    if 0 < len(m.groups()): 
        #        dbtno = 100 * int(m.group(1))
        #        if 1 < len(m.groups()): 
        #            dbtno = dbtno + int(m.group(2))
        #            dbtcode = str(dbtno).zfill(5)
        
        dbtcode = ''
        value = value.replace('\t', '').replace(' ', '')
        p = value.split('.')
        p1 = 0
        p2 = 0
        p3 = 0
        if 0 < len(p):
            p1 = 10000 * int(p[0])
            if 1 < len(p):
                p2 = 100 * int(p[1])
                if 2 < len(p):
                    p3 = 10 * int(p[2])
        dbtcode = str(p1 + p2 + p3).zfill(7)
        return dbtcode
        
        
    def add_field_type(self, table_name, field_name, field_type):
        table_name = table_name.lower().replace(' ', '_').replace('\t', '_').replace('__', '_')
        field_name = field_name.lower().replace(' ', '_').replace('\t', '_').replace('__', '_')
        field_type = self.get_associated_domain(field_type)
        if '<REF>' == field_type:
            field_type = ''
        if '' <> field_type:
            reftype_key = table_name + '::' + field_name
            self.__base_types[reftype_key] = field_type
            #debug('> ' + reftype_key + ' -> ' + field_type)


    def get_field_type(self, table_name, field_name):
        table_name = table_name.lower().replace(' ', '_').replace('\t', '_').replace('__', '_')
        field_name = field_name.lower().replace(' ', '_').replace('\t', '_').replace('__', '_')
        reftype_key = table_name + '::' + field_name
        if reftype_key in self.__base_types:
            return self.__base_types[reftype_key]
        return '<NOTYPE>'
        
        
    def collect_base_types(self):
        block = []
        cur_tab_name = ''
        cur_tab_no = 0
        pre_tab_no = 0
        cur_field_names = []

        #re_tbd_header_break = re.compile('==DBT#(\d+)', re.IGNORECASE)
        re_tbd_header_break = re.compile('==DBT#(.*)', re.IGNORECASE)
        
        for lineitem in self.__lines:
            line = self.strip_line(lineitem)

            if line.startswith('----'):
                continue
          
            field_name = ''
            field_type = ''
            dbtcode = ''
            break_tab_no = 0;    
            #print(line)
          
            m = re_tbd_header_break.match(line)
            if m is not None:
                #debug('DBT BREAK DETECTED (1)')
                dbtcodepart = m.group(1)
                dbtcode = self.get_dbt_code(dbtcodepart)
                break_tab_no = int(dbtcode)
                # debug('DBT BREAK DETECTED "' + dbtcode + '" (2)')
        
            if dbtcode != '':
                if break_tab_no < cur_tab_no:
                    debug('TABLE ENUMERATION MISMATCH (1)' + str(cur_tab_no) + ':' + str(break_tab_no))
                    return
                if 3 < len(block):
                    if '' == cur_tab_name:
                        debug('TABLE NAME MISMATCH "' + line + '" (1)')
                        return
                    
                    field_num = block[0]
                    if not field_num.isdigit():
                        debug('FIELD NO MISMATCH (1)')
                        print(block)
                        return
                    field_no = int(field_num)
                    if (field_no <> len (cur_field_names) + 1):
                        debug('FIELD COUNTING MISMATCH (1)')
                        print(block)
                        return
                    
                    field_name = block[2].lower()
                    field_type = block[3]
                    
                    if field_name in cur_field_names:
                        debug('DUPLICATE FIELD NAME "' + cur_tab_name + '::' + field_name + '" (1)')
                        return
                    cur_field_names.append(field_name)
                    
                    self.add_field_type(cur_tab_name, field_name, field_type)
                    
                    domain = self.get_associated_domain(field_type);
                    if '<REF>' == domain:
                        if (6 > len(block)):
                            print(block)
                            debug('NOT ENOUGHT REFERENCE TABLE! (1)')
                    else:
                        field_type = self.get_field_type(cur_tab_name, field_name)
                    debug('FIELD: ' + cur_tab_name + '::' + field_name + ' [' + field_type + '] (1)')
                    
                    block = []
                #else:
                #    debug('CAPTION ONLY "' + line + '"')
                cur_tab_no = int(dbtcode)
                cur_field_names = []
                continue
        
            elif line == '':
            
                if 1 == len(block):
                    #debug('*** if 1 == len(block):')
                    dbtcodepart = block[0]
                    temp_dbtcode = self.get_dbt_code(dbtcodepart)
                    temp_tab_no = int(temp_dbtcode)
                    if cur_tab_no <> temp_tab_no:
                        debug('TABLE ENUMERATION MISMATCH (2) ' + str(cur_tab_no) + ':' + str(temp_tab_no))
                        return
                    block = []
                            
                elif 2 == len(block):
                    cur_tab_caption = block[0].replace('\t', ' ')
                    cur_tab_name = block[1].lower().replace(' ', '_').replace('\t', '_').replace('__', '_')
                    if (cur_tab_name.startswith('(')) and (cur_tab_name.endswith(')')):
                        cur_tab_name = cur_tab_name[1:-1]
                    if cur_tab_name in self.__tab_names.values():
                        debug('TABLE NAME DUPE "' + cur_tab_name + '" (1)')
                        return
                    self.__tab_names[cur_tab_no] = cur_tab_name
                    debug('TABLE: ' + cur_tab_name + ' (1)')
                    #debug('TABLE :' + str(cur_tab_no) + ' ' + cur_tab_name + ' ' + cur_tab_caption + ' (1)')
                    block = []
                    cur_field_names = []
                    
                elif 3 == len(block):
                    #debug('*** elif 3 == len(block):')
                    dbtcodepart = block[0]
                    temp_dbtcode = self.get_dbt_code(dbtcodepart)
                    temp_tab_no = int(temp_dbtcode)
                    if cur_tab_no <> temp_tab_no:
                        debug('TABLE ENUMERATION MISMATCH (3) ' + str(cur_tab_no) + ':' + str(temp_tab_no))
                        return
                      
                    cur_tab_caption = block[1]
                    cur_tab_name = block[2]
                    if (cur_tab_name.startswith('(')) and (cur_tab_name.endswith(')')):
                        cur_tab_name = cur_tab_name[1:-1]
                    if cur_tab_name in self.__tab_names.values():
                        debug('TABLE NAME DUPE "' + cur_tab_name + '" (2)')
                        return
                    self.__tab_names[cur_tab_no] = cur_tab_name
                    debug('TABLE: ' + cur_tab_name + ' (2)')
                    #debug('TABLE :' + str(cur_tab_no) + ' ' + cur_tab_name + ' ' + cur_tab_caption + ' (1)')
                    block = []
                    cur_field_names = []
                  
                elif 3 < len(block):
                    if '' == cur_tab_name:
                        debug('TABLE NAME MISMATCH "' + line + '" (2)')
                        return

                    field_num = block[0]
                    if not field_num.isdigit():
                        debug('FIELD NO MISMATCH (2)')
                        print(block)
                        return
                    field_no = int(field_num)
                    if (field_no <> len (cur_field_names) + 1):
                        debug('FIELD COUNTING MISMATCH (2)')
                        print(block)
                        return
                        
                    field_name = block[2].lower()
                    field_type = block[3]
                    
                    if field_name in cur_field_names:
                        debug('DUPLICATE FIELD NAME "' + cur_tab_name + '::' + field_name + '" (2)')
                        return
                    cur_field_names.append(field_name)

                    self.add_field_type(cur_tab_name, field_name, field_type)
                    
                    domain = self.get_associated_domain(field_type);
                    if '<REF>' == domain:
                        if (6 > len(block)):
                            print(block)
                            debug('NOT ENOUGHT REFERENCE TABLE! (2)')
                            return
                    else:
                        field_type = self.get_field_type(cur_tab_name, field_name)
                    debug('FIELD: ' + cur_tab_name + '::' + field_name + ' [' + field_type + '] (2)')
                    
                    block = []

            else:  
                block.append(line)


    def process_field_block(self, block): 
        #debug('>> process_field_block')
        if self.__current_table is None:
            print(block)
            raise Exception('TABLE OBJECT MISMATCH (BLOCK)') 
        if '' == self.__current_table.name:
            print(block)
            raise Exception('TABLE NAME MISMATCH (BLOCK)') 
        field_num = block[0]
        if not field_num.isdigit():
            print(block)
            raise Exception('FIELD NO MISMATCH') 
        
        field_no = int(field_num)
        if (field_no <> len (self.__current_table.fields) + 1):
            print(block)
            raise Exception('FIELD COUNTING MISMATCH') 
        
        field_caption = block[1].replace('\t', ' ').replace('  ', ' ')
        if '' == field_caption:
            print(block)
            raise Exception('FIELD CAPTION MISMATCH') 
        
        field_name = block[2].lower().replace('\t', ' ').replace(' ', '_').replace('__', '_')
        if '' == field_caption:
            print(block)
            raise Exception('FIELD NAME MISMATCH') 
         
        field_type = block[3].lower().replace('\t', ' ').replace(' ', '_').replace('__', '_')
            
        #field_type = self.get_field_type(self.__current_table.name, field_name)
            
        field_type = self.get_associated_domain(field_type);
        
        #if 'id_obkon' == field_name:
        #    debug(field_type)

        ref_table_name = ''
        ref_field_name = ''
        
        if '<REF>' == field_type:
            ref_table_code = block[5]
            if '' == ref_table_code:
                print(block)
                raise Exception('REFERENCE CODE ERROR') 
            
            ref_table_code = ref_table_code.replace('@@DBT#', '')
            
            #debug(ref_table_code)
            
            ref_table_code = self.get_dbt_code(ref_table_code)
            ref_table_no = int(ref_table_code)
            ref_table_name = self.__tab_names[ref_table_no]
            ref_field_name = field_name
            
            field_type = self.get_field_type(ref_table_name, ref_field_name)
            
            #if 'id_obkon' == field_name:
            #    debug(str(ref_table_no))
            #    debug(str(ref_table_name))
            
            fk_key_name = 'fk_' + self.__current_table.name + '_' + field_name + '_' + ref_table_name + '_' + ref_field_name
            field_list = [field_name]
            ref_field_list = [field_name]
            self.__current_table.add_fk(fk_key_name, field_list, ref_table_name, ref_field_list, 'on update cascade', 'on delete cascade')


    
            #uk_key_name = 'pk_' + ref_table_name + '_' + ref_field_name;
            #__uk_keys
            
            
            

        if '' == ref_table_name:
            debug('NEW FIELD "' + self.__current_table.name + '::' + field_name + '" ' + field_type + ' ')
        else:
            debug('NEW FIELD "' + self.__current_table.name + '::' + field_name + '" ' + field_type + ' (' + ref_table_name + ':' + ref_field_name + ')')
                                                         
        self.__current_table.add_field(field_name, field_type, True, field_caption)
        self.descriptionary.addfield(self.__current_table.name, field_name, field_caption)
        
                
    def process_table_block(self, block): 
        #debug('>> process_table_block')
        tab_num = -1
        tab_code = self.__current_table_code
        tab_caption = ''
        tab_name = ''
        
        if 2 == len(block):
            tab_num = int(tab_code)
            tab_caption = block[0]
            tab_name = block[1]
            
        if 3 == len(block):
            tab_code = self.get_dbt_code(block[0])
            tab_num = int(tab_code)
            tab_caption = block[1]
            tab_name = block[2]
            
        if tab_num <> int(tab_code):
            print(block)
            raise Exception('TABLE COUNTING ERROR ' + str(tab_num) + ' - ' + str(int(tab_code))) 
            
        tab_name = tab_name.lower().replace('\t', ' ').replace(' ', '_').replace('__', '_')
        
        if (tab_name.startswith('(')) and (tab_name.endswith(')')):
            tab_name = tab_name[1:-1]

        if self.__current_table is None:
            debug('NEW TABLE :' + tab_name + ' / ' + tab_caption + ' [' + tab_code + ']')
            self.__current_table = Table(tab_name, tab_caption + ' [' + tab_code + ']');
        else:
            print(block)
            raise Exception('TABLE INIT MISMATCH') 
        
        
    def fixate_current_table(self): 
        #debug('>> fixate_current_table')
        if self.__current_table is None:
            raise Exception('TABLE OBJECT MISMATCH (FIXATE)') 
        if '' == self.__current_table.name:
            raise Exception('TABLE NAME MISMATCH (FIXATE)') 
        self.tables[self.__current_table.name] = self.__current_table
        self.__current_table = None
                

    def process_blocks(self): 
        block = []
        re_tbd_header_break = re.compile('==DBT#(.*)', re.IGNORECASE)
        for lineitem in self.__lines:
            line = self.strip_line(lineitem)
            if line.startswith('----'):
                continue
            dbtcode = ''
            #print(line)
            m = re_tbd_header_break.match(line)
            if m is not None:
                dbtcodepart = m.group(1)
                dbtcode = self.get_dbt_code(dbtcodepart)
            if dbtcode != '':
                #debug('CODE: ' + dbtcode)
                if 3 < len(block):
                    self.process_field_block(block)
                    block = []
                if '' <> self.__current_table_code:
                    self.fixate_current_table()
                self.__current_table_code = dbtcode
            elif line == '':
                if (2 == len(block)) or (3 == len(block)):
                    self.process_table_block(block)
                    block = []
                elif 3 < len(block):
                    self.process_field_block(block)
                    block = []
            else:  
                block.append(line)


    def process_blocks_temp(self): 

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
                    field_type = self.get_associated_domain(field_type)

                    # print('T' + tab_no + ' ' + cur_tab_name + '  ' + field_name + ' ' + field_type)

                    ref_table_name = '<TABLE>'
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
                                ref_table_no = table_ref;
                                ref_table_name = self.__tab_names[int(ref_table_no)]
                                base_type_key = ref_table_name + '::' + ref_field_name
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
                        fk_key_name = 'fk_' + cur_tab_name + '_' + field_name + '_' + ref_table_name + '_' + ref_field_name
                        field_list = [field_name]
                        ref_field_list = [field_name]
                        table.add_fk(fk_key_name, field_list, ref_table_name, ref_field_list, 'cascade', 'cascade')
                      
                    block = []
            else:  
                block.append(line)
              
        print('\n' * 3)

        for t in self.tables:
            print(t)
            for f in table.fields:
                print('  ' + f.name + '  ' + f.data_type)
          


