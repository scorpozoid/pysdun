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

# TODO: Сделать для триггеров и хранимых процедур сначала create пустого, а потом alter и в alter-е уже включить мясо
#

import textwrap
import datetime
import codecs
import re
import os
import ibe_ddl

from os import path


# PYSDUN - PYthon Schema/structure of Database UNificator
# Convert IbeSchema to Microsoft SQLServer script
class PysdunMssql:

    def __init__(self, schema):
        self.schema = schema

    @staticmethod
    def unident(string):
        if string and string[0] == '\n':
            string = string[1:]
        return textwrap.dedent(string)

    @staticmethod
    def replace_data_type(data_type):
        blob_bin = 'varbinary(max)'
        blob_memo = 'varchar(max)'
        gr_sub_type = 'gr_sub_type'
        gr_segment_size = 'gr_segment_size'
        regex_blob = 'blob(?:\s+sub_type\s+(?P<{}>\d+))(?:\s+segment\s+size\s+(?P<{}>\d+))'.format(
            gr_sub_type, gr_segment_size
        )
        re_blob = re.compile(regex_blob, re.IGNORECASE)

        mdt = re_blob.match(data_type)
        if mdt:
            data_type = 'varchar(max)'
            # print(mdt.groupdict())
            if gr_sub_type in mdt.groupdict():
                sub_type = mdt.groupdict()[gr_sub_type]
                sub_types = {
                    '0': blob_bin,
                    '1': blob_memo
                }
                if sub_type in sub_types:
                    data_type = sub_types[sub_type]
                else:
                    data_type = blob_bin
                    
        # Тип данных timestamp - это синоним к типу данных rowversion и не предназначен для хранения даты и времени
        # поэтому недо заменить его на datetime (или datetime2), тем более что
        # GETDATE() в MSSQL работает только с полями типа datetime, с timestamp-полями - не работает

        if not data_type.startswith('t_'):
            data_type = re.sub('timestamp', 'datetime', data_type, flags=re.I)
            data_type = re.sub('boolean', 'bit', data_type, flags=re.I)

        data_type = re.sub('numeric\(18,\s*0\)', 'bigint', data_type, flags=re.I)
        data_type = re.sub('default\s+false', 'default 0', data_type, flags=re.I)
        data_type = re.sub('default\s+true', 'default 1', data_type, flags=re.I)

        data_type = re.sub("'now'", 'getdate()', data_type, flags=re.I)

        return data_type

    def export(self, filename):
        ddl_header = []
        # ddl_sequences = []
        ddl_udt = []  # user defined types aka domain
        ddl_tables = []
        ddl_views = []
        ddl_indices = []
        ddl_pk = []
        ddl_uk = []
        ddl_fk = []
        ddl_stored_procedures = {}
        ddl_triggers = []
        sql_data = []  # inserts

        #
        # sequences = set()
        # for generator in self.schema.generators:
        #    sequence_name = generator.name
        #    sequences.add(sequence_name)

        # mssql-2012 or higher
        # for sequence in sequences:
        #    ddl_sequences.append('create sequence {0}'.format(sequence))

        if self.schema.domains:
            for domain in self.schema.domains:
                data_type = PysdunMssql.replace_data_type(domain.data_type)
                domain_name = domain.name
                ddl_udt.append('create type {0} from {1}'.format(domain_name, data_type))
        #
        for table_name in self.schema.tables:
            table = self.schema.tables[table_name]
            field_list = []
            for field in table.fields:
                serial = ''
                not_null = 'not null'
                default = ''
                data_type = self.replace_data_type(field.data_type)
                if field.nullable:
                    not_null = ""
                for domain in self.schema.domains:
                    if field.data_type.lower() == domain.name.lower():
                        if domain.autoinc:
                            # serial = 'identity (1, 1)'
                            serial = 'identity'
                            # [i] for mssql-2012 and higher:
                            # for generator in self.schema.generators:
                            #     if generator.is_ownered_by(table_name, field.name):
                            #         serial = ''
                            #         default = "default next value for {}".format(generator.name)
                            #         break
                            # if serial != '':  # found default sequence
                            #     data_type = ''
                            #     not_null = ''
                        break
                # [w] "data_type" and "serial" exchanged in compare with pgsql
                field_item = '{} {} {} {} {}'.format(field.name, data_type, serial, not_null, default)
                field_item = ibe_ddl.strip_statement(field_item)
                field_list.append(field_item)

            template = 'create table {} ({})'
            table_statement = template.format(
                table.name,
                ', '.join([str(f) for f in field_list]))
            ddl_tables.append(table_statement)
        #
        for table_name in self.schema.tables:
            table = self.schema.tables[table_name]
            if table.x is not None:
                for x_name in table.x:
                    field_list = table.x[x_name][0]
                    order = table.x[x_name][1]
                    unique = table.x[x_name][2]
                    if order is None:
                        order = ''
                    if unique is None:
                        unique = ''
                    index_statement = 'create {} index {} on {} ({})'.format(
                        unique, x_name, table_name,
                        ', '.join([str(f + ' ' + order) for f in field_list]))
                    index_statement = ibe_ddl.strip_statement(index_statement)
                    ddl_indices.append(index_statement)
            if table.uk is not None:
                for fk_name in table.uk:
                    field_list = table.uk[fk_name]
                    template = 'alter table {} add constraint {} unique ({})'
                    fk_statement = template.format(
                        table_name, fk_name,
                        ', '.join([str(f) for f in field_list]))
                    ddl_uk.append(fk_statement)
            if table.pk is not None:
                pk_name = 'pk_{}'.format(table_name)
                template = 'alter table {} add constraint {} primary key ({})'
                pk_statement = template.format(
                    table_name, pk_name,
                    ', '.join([str(f) for f in table.pk]))
                ddl_pk.append(pk_statement)
        #
        for table_name in self.schema.tables:
            table = self.schema.tables[table_name]
            if table.fk is not None:
                for fk_name in table.fk:
                    field_list = table.fk[fk_name][0]
                    ref_table_name = table.fk[fk_name][1]
                    ref_field_list = table.fk[fk_name][2]
                    del_rule = table.fk[fk_name][3]
                    upd_rule = table.fk[fk_name][4]
                    if del_rule is None:
                        del_rule = ""
                        # print('WARNING! NO ACTION! (' + fk_name + ':' + upd_rule + ')')
                        # upd_rule = "on update no action"
                    if upd_rule is None:
                        upd_rule = ""
                        # print('WARNING! NO ACTION! (' + fk_name + ':' + del_rule + ')')
                        # del_rule = "on delete no action"
                    if del_rule:
                        del_rule = del_rule.strip()
                    if upd_rule:
                        upd_rule = upd_rule.strip()
                    template = 'alter table {} add constraint {} foreign key ({}) references {} ({}) {} {}'
                    fk_statement = template.format(
                        table_name, fk_name,
                        ', '.join([str(f) for f in field_list]),
                        ref_table_name,
                        ', '.join([str(f) for f in ref_field_list]), del_rule, upd_rule)
                    fk_statement = ibe_ddl.strip_statement(fk_statement)
                    # dfpost patch
                    # fk_statement = fk_statement.replace('alter table navig', '-- alter table navig')
                    # fk_statement = fk_statement.replace('alter table pf_result', '-- alter table pf_result')
                    # fk_statement = fk_statement.replace('alter table worksession', '-- alter table worksession')
                    ddl_fk.append(fk_statement)

        #
        for view in self.schema.views[:]:
            ddl_views.append(view)

        #
        for procedure in self.schema.procedures:
            procedure_template = """
                use [{database_alias}]
                go

                if exists (select * from sys.objects where type = 'P' and name = '{procedure_name}')
                drop procedure {procedure_name}
                go

                create procedure {procedure_name}
                /*
                {input_parameters}
                */
                /*
                returns {output_parameters}
                */
                as
                begin
                  set nocount on;
                  /*
                  {procedure_body}
                  */
                end
                go
                """

            ddl_stored_procedures[procedure.name] = self.unident(procedure_template).format(
                database_alias=self.schema.alias,
                procedure_name=procedure.name,
                input_parameters='-- ' + procedure.pm_in,
                output_parameters='-- ' + procedure.pm_out,
                procedure_body='\n'.join(map(lambda body_line: '  -- ' + body_line, procedure.body))
            )

        #
        for trigger in self.schema.triggers[:]:
            ddl_trigger_template = """
                /* --- */
                if exists(
                  select * from dbo.sysobjects
                  where name = '{trigger_name}' and objectproperty(id, 'IsTrigger') = 1
                )
                  drop trigger {trigger_name}
                go

                create trigger {trigger_name} on {table_name} {trigger_place} as
                begin
                  set nocount on;
                  /*
                  {trigger_body}
                  */
                end
                go
                """

            ddl_triggers.append(
                self.unident(ddl_trigger_template).format(
                    trigger_name=trigger.name,
                    table_name=trigger.table,
                    trigger_place=trigger.place,
                    trigger_body='\n'.join(map(lambda body_line: '  -- ' + body_line, trigger.body))
                )
            )

        #
        for data in self.schema.data[:]:
            data_line = re.sub("'now'", 'getdate()', data, flags=re.I)
            # print(data_line)
            sql_data.append(data_line)


        # if not self.schema.host:
        #     self.schema.host = '127.0.0.1'
        ddl_header_template = """
            /*
             * --
             * -- {build_timestamp}
             * --
             * -- data_path = "C:\\Program Files\\Microsoft SQL Server\\MSSQL11.MSSQLSERVER\\MSSQL\\DATA"
             * -- use [{{master}}]
             * -- go
             * -- declare @data_path varchar(max) = '';
             * -- select @data_path = substring(physical_name, 1, charindex(N'{master}.mdf', lower(physical_name)) - 1)
             * -- from master.sys.master_files
             * -- where database_id = 1 and file_id = 1
             * -- print @data_path
             * -- go
             * --
             */
            use [{master}]
            if exists(select * from sys.databases where name = '{db_name}')
            begin
              print 'Database {db_name} exists'
              alter database {db_name} set offline with rollback immediate
              alter database {db_name} set online
              drop database {db_name}
            end
            else
            begin
              print 'Database {db_name} does not exists'
            end

            create database [{db_name}]
            go

            alter database [{db_name}] collate Cyrillic_General_CI_AS
            go

            use [{db_name}]
            go
            """

        ddl_header.append(
            self.unident(ddl_header_template).format(
                build_timestamp=datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"),
                master='master',
                db_name=self.schema.alias
            ))

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        go = 'go\n'
        crlf = '\n'

        filename_pair = path.splitext(filename)
        filename_file = filename_pair[0]
        filename_ext = filename_pair[1]

        file_encoding_utf8 = 'utf-8'
        file_encoding_win1251 = 'cp1251'

        file_encoding = file_encoding_win1251

        fn_main = filename
        fn_triggers = filename_file + '-triggers' + filename_ext
        fn_data = filename_file + '-data' + filename_ext
        fn_sp_template = '{0}-sp-{{stored_procedure_name}}.sql'.format(filename_file, filename_ext)
        fn_batch = filename_file + '.cmd'

        # # #
        # # #
        # # #
        f = codecs.open(fn_main, 'w', encoding=file_encoding)
        try:
            f.write('-- {} \n'.format(file_encoding))
            f.write('\n'.join(ddl_header[:]))
            # mssql-2012 or higher - f.write('\n'.join(sorted(ddl_sequences)))
            f.write('\n'.join(sorted(ddl_udt)))
            f.write(crlf)
            f.write(go)
            f.write('\n'.join(sorted(ddl_tables[:])))
            f.write(crlf)
            f.write('\n'.join(sorted(ddl_indices[:])))
            f.write(crlf)
            f.write('\n'.join(sorted(ddl_pk[:])))
            f.write(crlf)
            f.write('\n'.join((ddl_uk[:])))
            f.write(crlf)
            f.write('\n'.join((ddl_fk[:])))
            f.write(go)
            f.write(crlf)
            f.write('\n'.join(sorted(ddl_views[:])))
            f.write(go)
            f.write(crlf)
            f.write('/* EOF */\n')
        finally:
            f.close()

        # # #
        # # #
        # # #
        if os.path.isfile(fn_triggers):
            filename += '~'
        if os.path.isfile(fn_triggers):
            os.remove(fn_triggers)
        f = codecs.open(fn_triggers, 'w', encoding=file_encoding)
        try:
            f.write('-- {} \n'.format(file_encoding))
            f.write('use [{}]'.format(self.schema.alias))
            for trigger_item in sorted(ddl_triggers[:]):
                f.write(trigger_item)
            f.write('/* EOF */\n')
        finally:
            f.close()

        # # #
        # # #
        # # #
        for procedure_name in ddl_stored_procedures:
            procedure_item = ddl_stored_procedures[procedure_name]
            fn_sp = fn_sp_template.format(stored_procedure_name=procedure_name)
            if os.path.isfile(fn_sp):
                fn_sp += '~'
            if os.path.isfile(fn_sp):
                os.remove(fn_sp)
            f = codecs.open(fn_sp, 'w', encoding=file_encoding)
            try:
                f.write('-- {} \n'.format(file_encoding))
                f.write(procedure_item)
                f.write('/* EOF */\n')
            finally:
                f.close()

        # # #
        # # #
        # # #
        f = codecs.open(fn_data, 'w', encoding=file_encoding)
        try:
            f.write('-- {} \n'.format(file_encoding))
            f.write('use [{}]\n'.format(self.schema.alias))
            for data_item in sql_data[:]:
                f.write(data_item + '\n')
            f.write(go)
            f.write('/* EOF */\n')
        finally:
            f.close()

        # # #
        # # #
        # # #
        isql = "sqlcmd -S %MSSQL_HOST% -U %MSSQL_USERNAME% -P %MSSQL_PASSWORD%"
        batch_template = """
            @echo off
            rem
            rem {file_encoding}
            rem

            set MSSQL_USERNAME={db_user}
            set MSSQL_HOST={db_host}
            set MSSQL_PASSWORD={db_password}
            rem 192.168.128.207 1Masterkey

            rem {sqlcmd} -Q "alter database {db_alias} set offline with rollback immediate"
            rem {sqlcmd} -Q "alter database {db_alias} set online"
            rem {sqlcmd} -i script.sql -o script.log

            {sqlcmd} -i {script_name_main}
            {script_procedure}
            {sqlcmd} -i {script_name_triggers}
            {sqlcmd} -i {script_name_data}

            rem bcp {db_alias}.dbo.job out "{db_alias}.txt" -c -T
            rem echo "OK"
            pause
            """

        f = codecs.open(fn_batch, 'w', encoding=file_encoding)
        try:
            procedure_block = []
            for procedure_name in ddl_stored_procedures:
                procedure_block.append(
                    "{sqlcmd} -i {sqlscript}".format(
                        sqlcmd=isql,
                        sqlscript=path.basename(fn_sp_template.format(stored_procedure_name=procedure_name))
                    )
                )

            f.write(
                self.unident(batch_template).format(
                    file_encoding=file_encoding,
                    db_host=self.schema.host,
                    db_user='sa',
                    db_password=self.schema.password,
                    db_alias=self.schema.alias,
                    sqlcmd=isql,
                    script_name_main=path.basename(fn_main),
                    script_name_triggers=path.basename(fn_triggers),
                    script_name_data=path.basename(fn_data),
                    script_procedure='\n'.join(procedure_block)
                )
            )
        finally:
            f.close()


