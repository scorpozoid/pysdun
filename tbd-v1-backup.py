#!/usr/bin/python
# -*- coding: utf-8 -*- 

#
# Целое размерностью 5, 10, 18, 20, 50, 500?
# таб 19 = Vzaim_VzSr
# таб 52, за ней стразу таб 52
# почему коорд только с.ш. и в.д
# таб 49, поле 5 нет размерности
# таб 51, пропуск в нумерации
# 4 naliv - Вводится мышью на карте
# таб 43, поле 6 dig_sign
# таб 43, поле 14 order_mark
# т 53, п 6
# Численное и Числовое - в чем разница
# т 22, п 8, lost number
# Строка и Символьное - в чем разница
# ID_Histor - без указания таблицы базы
# t 53, nom_tohki, koord_tohki
# 

import sys
import re
import codecs
import os
import getopt

from ibe_ddl import Table

#def is_num(v):
#  try:
#    int(v)
#    return True
#  except ValueError:
#    return False
    
reftype = {}
reftable = {}



def get_field_type(value):
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
		

def collect_reftype(lines):
	block = []
	curtable = ''
	tabno = ''
	pretabno = 0
	for lineitem in lines:
		line = lineitem.strip().rstrip('\r').rstrip('\n')
		if line == "":
			if 0 < len(block):
				if 1 == len(block):
					if not block[0].isdigit():
						print ('NONDIGIT ' + block[0])
						block = []
				if 3 == len(block):
					tabno = block[0]
					curtable = block[2].lower()
					curtable = curtable.replace(' ', '_')
					if (curtable.startswith('(')) and (curtable.endswith(')')):
						curtable = curtable[1:-1]
					reftable[int(tabno)] = curtable
					block = []
					if int(tabno) == int(pretabno + 1):
						pretabno = int(tabno)
					else:
						print(u'TABLE ORDERING MISMATCH ' + tabno + ' ' + str(pretabno))
				elif 3 < len(block):
					field_name = block[2].lower().replace(' ', '_')
					field_type = block[3].lower().replace(' ', '')
					
					field_type = get_field_type(field_type)
					
					if '<REF>' == field_type:
						field_type = ''
					
					if '' <> field_type:
						reftype_key = curtable + '::' + field_name
						reftype[reftype_key] = field_type
						print('>' + reftype_key + ' -> ' + field_type)
						
					block = []
		else:  
			block.append(line)


def main(): 
	filename = "tbd.txt"
	# [ok] lines = [line for line in codecs.open(filename, encoding='utf-8')]
	# [ok] print(lines)
	file = codecs.open(filename, encoding='utf-8')
	lines = file.readlines()

	collect_reftype(lines)

	tables = []

	block = []
	state = 0
	curtabname = ''
	
	table = None;
	
	for lineitem in lines:
		line = lineitem.strip().rstrip('\r').rstrip('\n')
		if line == "":
			if 0 < len(block):
				if 1 == len(block):
					tabnum = block[0]
					if not tabnum.isdigit():
						block = []
				if 3 == len(block):
					if not table is None:
						tables.append(table)

					tabnum = block[0]
					tabcaption = block[1]
					tabname = block[2].lower()
					tabname = tabname.replace(' ', '_')
					if (tabname.startswith('(')) and (tabname.endswith(')')):
						tabname = tabname[1:-1]
					curtabname = tabname
					
					table = Table(tabname, tabcaption + ' [' + tabnum + ']');
					
					# print('T' + tabnum + ' ' + tabname + '  ' + tabcaption)
					# print('tab #{0} - {1}'.format(block[0], block[1]))
					# print('tab #{0}'.format(unicode(block[0])))
					block = []
				elif 3 < len(block):
					field_num = block[0]
					field_caption = block[1]
					field_name = block[2].lower().replace(' ', '_')
					field_type = block[3].lower().replace(' ', '')
					
					field_len = 0
					field_ref = ''
					
					field_type = get_field_type(field_type)

					print('T' + tabnum + ' ' + curtabname + '  ' + field_name + ' ' + field_type)

					reftab = ''
					reffield = field_name

					if '<REF>' == field_type:
						table_ref = ''
						
						if 'ID_Histor'.lower() == field_name and 6 > len(block):
							table_ref = u'БД № 6'

						if table_ref == '':
							if 5 < len(block):
								table_ref = block[5]
							else:
								table_ref = ''
								print('* ' + curtabname)
								print('WRONG LINE COUNT ' + str(len(block)))
								for b in block:
									print(b)
								
						if table_ref <> '':
							table_ref = table_ref.replace(u'DBNO', '');
							table_ref = table_ref.replace(u'БД', '');
							table_ref = table_ref.replace(u'№', '');
							table_ref = table_ref.strip();
							if table_ref.isdigit():
								ref_tab_no = table_ref;
								reftab = reftable[int(ref_tab_no)]
								reftypekey = reftab + '::' + reffield
								if reftypekey in reftype:
									field_type = reftype[reftypekey]
								else:
									print('NO REFERENCE FOR "' + reftypekey + '"')
									field_type = 'int_t'
							else:
								print('WRONG REFERENCE NO "' + table_ref + '"')
								field_type = 'int_t'
					
					if field_type == '':
						field_type = block[3].strip().lower()
					
					table.add_field(field_name, field_type, False, field_caption)
					
					if '<REF>' == field_type:
						fk_key_name = 'fk_' + curtabname + '_' + field_name + '_' + reftab + '_' + reffield
						field_list = [field_name]
						ref_field_list = [field_name]
						table.add_fk(fk_key_name, field_list, reftab, ref_field_list, 'restrict', 'restrict')
						
					# print('f' + .lower() + ' ' + block[2].lower() + ' (' + field_type + ') ' + block[1])
					# print('field #{0} {1}'.format(block[0], block[1]))
					block = []
		else:  
			block.append(line)
			
	print('\n' * 3)

	for table in tables:
		print(table)
		for field in table.fields:
			print('  ' + field.name + '  ' + field.data_type)
  
if __name__ == "__main__":
  main()	