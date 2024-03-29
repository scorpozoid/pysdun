#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# 
# 2018-04-29 [!] TODO: use SQLAlchemy instead of bicycle engineering
# 2015-04-20 [!] TODO: use SQLAlchemy instead of bicycle engineering
# 2013.11.07 [+] Initial release, refactoring of ibsql2pgsql.py
#                
# 
#


def strip_statement(value):
    value = value.replace('  ', ' ')
    value = value.replace(' ;', ';')
    value = value.strip()
    return value


class Field:
    def __init__(self, field_name, field_type, nullable, description):
        self.name = field_name
        self.data_type = field_type
        self.nullable = nullable
        self.description = description

    def __str__(self):
        if self.nullable:
            return "{} {}".format(self.name.strip(), self.data_type.strip())
        else:
            return "{} {} not null".format(self.name.strip(), self.data_type.strip())
    

class Table:
    def __init__(self, table_name, description):
        self.name = table_name
        self.description = description
        self.fields = []
        self.pk = None
        self.fk = None
        self.uk = None
        self.x = None  # indices (indexes)
        # debug('>' + name + ': ' + self.description)

    def __str__(self):
        result = ''
        #for field in fields:
        #  result += field.name + ' '
        return self.name + result

    def add_field(self, field_name, field_type, is_nullable, field_description):
        self.fields.append(Field(field_name, field_type, is_nullable, field_description))

    def add_pk(self, key_name, field_list):
        self.pk = field_list

    def add_fk(self, key_name, field_list, reference_table, reference_field_list, delete_rule, update_rule):
        if self.fk is None:
            self.fk = {}
        self.fk[key_name] = [field_list, reference_table, reference_field_list, delete_rule, update_rule]

    def add_uk(self, key_name, field_list):
        if self.uk is None:
            self.uk = {}
        self.uk[key_name] = field_list

    def add_index(self, index_name, field_list, order, is_unique):
        if self.x is None:
            self.x = {}
        self.x[index_name] = [field_list, order, is_unique]


# 
class Generator:

    @staticmethod
    def __owner_key(table, field):
        return '{}::{}'.format(table, field).lower()

    def __init__(self, name):
        self.owners = []
        self.name = name

    def add_owner(self, table, field):
        #self.owners.append(field + '@'+ table)
        owner = self.__owner_key(table, field)
        self.owners.append(owner)

    def is_ownered_by(self, table, field):
        for owner in self.owners:
            if owner == self.__owner_key(table, field):
                return True
        return False


# 
class Domain:    
    def __init__(self, domain_name, data_type, autoinc):
        self.tabs = []
        self.name = domain_name
        self.data_type = data_type
        self.autoinc = autoinc


class StoredProcedure:
    def __init__(self, sp_name):
        self.name = sp_name
        self.pm_in = ''
        self.pm_out = ''
        self.body = []


class Trigger:
    def __init__(self, tr_name):
        self.name = tr_name
        self.table = ''
        self.place = ''
        self.position = 0
        self.body = []


class Schema:
    def __init__(self):
        self.generators = []
        self.domains = []
        self.tables = {}  # hash!
        self.views = []
        self.triggers = []
        self.procedures = []
        self.data = []
        self.host = ''
        self.alias = ''
        self.username = ''
        self.password = ''
        self.descriptionary = Descriptionary()

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

