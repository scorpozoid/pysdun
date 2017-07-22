#!/usr/bin/python
# -*- coding: utf-8 -*- 

#
# Целое размерностью 5, 10, 18, 20, 50, 500?
# таб 19 = Vzaim_VzSr
# таб 52, за ней стразу таб 52
# почему коорд только с.ш. и в.д
# таб 49, поле 5 нет размерности
# таб 51, пропуск в нумерации
# 4 naliv - Вводится мышью на карте (-;
# таб 43, поле 6 dig_sign
# таб 43, поле 14 order_mark
# т 53, п 6
# Численное и Числовое - в чем разница
# т 22, п 8, lost number
# Строка и Символьное - в чем разница
# ID_Histor - без указания таблицы базы
# t 53, nom_tohki, koord_tohki
# ID_OK_p - Код местоположения или Код объекта контроля
#


import sys
import re
import codecs
import os
import getopt

from tbd_schema import TdbIndieSchema
from pn_pgsql import PysdunPgsql

def main(): 
	filename = "tbd.txt"
	schema = TdbIndieSchema(filename)
	print(schema)
	pysdun = PysdunPgsql(schema)
	pysdun.export("tbd.sql")
	

if __name__ == "__main__":
    main()	
