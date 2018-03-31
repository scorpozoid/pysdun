#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PgSchema class load PostgreSQL dump to Schema class
#
#

import sys
import re
import codecs
import os

from os import path

import ibe_ddl
from ibe_ddl import Schema
from ibe_ddl import Generator
from ibe_ddl import Domain
from ibe_ddl import Table
from ibe_ddl import StoredProcedure
from ibe_ddl import Trigger


class PgSchema(Schema):

    def __init__(self, filename):
        Schema.__init__(self)
        #self.__re_set_term = None
        #self.__lines = []
        #self.__statements = []
        #self.load(filename)
