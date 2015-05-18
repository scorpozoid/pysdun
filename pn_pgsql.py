#!/usr/bin/env python
#!/usr/bin/python

import re
import codecs
import os
import textwrap

from os import path

import ibe_ddl


# PYSDUN - PYthon Schema/structure of Database UNificator
# Convert IbeSchema to PostgreSQL script
class PysdunPgsql:

    def __init__(self, schema):
        self.schema = schema

    @staticmethod
    def unident(string):
        if string and string[0] == '\n':
            string = string[1:]
        return textwrap.dedent(string)

    @staticmethod
    def ugly_patch_replace_binary(value):
        result = value
        result = result.replace('binary', 't_binary')
        result = result.replace('t_t_binary', 't_binary')
        return result

    @staticmethod
    def ugly_patch_replace_offset(value):
        result = value
        result = result.replace('.offset,', '."offset",')
        result = result.replace(' offset,', ' "offset",')
        result = result.replace(' offset ', ' "offset" ', )
        # [!] don't do it w/o huge testing:
        #     result = re.sub("[\s+\.]offset[;\s+\,]", ' "offfset" ', result, flags=re.I)
        return result

    @staticmethod
    def ugly_patch_replace_dvbservice_sequence(value):
        if value == 'dvbservice':
            return 'dvbservice_seq'
        return value

    @staticmethod
    def replace_data_type(data_type):
        blob_bin = 'text'  # [!] 'bytea'
        blob_memo = 'text'
        gr_sub_type = 'gr_sub_type'
        gr_segment_size = 'gr_segment_size'
        regex_blob = 'blob(?:\s+sub_type\s+(?P<{}>\d+))(?:\s+segment\s+size\s+(?P<{}>\d+))'.format(
            gr_sub_type, gr_segment_size
        )
        re_blob = re.compile(regex_blob, re.IGNORECASE)

        mdt = re_blob.match(data_type)
        if mdt:
            data_type = 'blob'
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
        data_type = re.sub('datetime', 'timestamp', data_type, flags=re.I)
        data_type = re.sub("'now'", 'current_timestamp', data_type, flags=re.I)
        data_type = re.sub('numeric\(18,\s*0\)', 'bigint', data_type, flags=re.I)

        data_type = PysdunPgsql.ugly_patch_replace_binary(data_type)
        return data_type

    def export(self, filename):
        ddl_header = []
        ddl_sequences = []
        ddl_domains = []
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
        sequences = set()
        for generator in self.schema.generators:
            sequence_name = generator.name
            sequence_name = self.ugly_patch_replace_dvbservice_sequence(sequence_name)
            sequences.add(sequence_name)
        #
        for sequence in sequences:
            ddl_sequences.append('create sequence {0};'.format(sequence))

        if self.schema.domains:
            for domain in self.schema.domains:
                data_type = self.replace_data_type(domain.data_type)

                domain_name = domain.name
                domain_name = self.ugly_patch_replace_binary(domain_name)
                ddl_domains.append('create domain {0} as {1};'.format(domain_name, data_type))
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
                            # serial = 'serial'
                            serial = 'bigserial'
                            for generator in self.schema.generators:
                                if generator.is_ownered_by(table_name, field.name):
                                    serial = ''
                                    default = "default nextval('{}')".format(generator.name)
                                    break
                            if serial != '':  # found default sequence
                                data_type = ''
                                not_null = ''
                        break
                field_item = '{} {} {} {} {}'.format(field.name, serial, data_type, not_null, default)
                field_item = ibe_ddl.strip_statement(field_item)

                field_list.append(field_item)
            template = 'create table {} ({});'
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
                    index_statement = 'create {} index {} on {} ({});'.format(
                        unique, x_name, table_name,
                        ', '.join([str(f + ' ' + order) for f in field_list]))
                    index_statement = ibe_ddl.strip_statement(index_statement)
                    ddl_indices.append(index_statement)
            if table.uk is not None:
                for fk_name in table.uk:
                    field_list = table.uk[fk_name]
                    template = 'alter table {} add constraint {} unique ({});'
                    fk_statement = template.format(
                        table_name, fk_name,
                        ', '.join([str(f) for f in field_list]))
                    ddl_uk.append(fk_statement)
            if table.pk is not None:
                pk_name = 'pk_{}'.format(table_name)
                template = 'alter table {} add constraint {} primary key ({});'
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
                    template = 'alter table {} add constraint {} foreign key ({}) references {} ({}) {} {};'
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
                    ddl_fk.append(fk_statement + ';')
        #
        for view in self.schema.views:
            ddl_views.append(view + ';')

        #
        for procedure in self.schema.procedures:
            function_template = """
                --
                -- create type t_{function_name} as (
                --   col1 int,
                --   col2 int
                -- );
                --

                create or replace function {function_name}()
                returns void
                -- returns setof t_{function_name}
                -- returns setof {function_name}_view
                -- returns table (col1 int, col2 text)
                -- returns setof record
                -- returns opaque
                as
                $$
                begin
                --  declare
                --    r {function_name}_view%rowtype;
                --    r t_{function_name}%rowtype;
                --  /*
                {function_body}
                --  */
                end
                $$
                language 'plpgsql'
                immutable /* immutable | stable */
                ;
                """

            function_block = self.unident(function_template).format(
                function_name=procedure.name,
                function_body='\n'.join(map(lambda body_line: '--  ' + body_line, procedure.body))
            )

            ddl_stored_procedures[procedure.name] = function_block

        for trigger in self.schema.triggers:
            trigger_template = """
                create or replace function trf_{trigger_name}() returns trigger /* trigger | opaque */
                as
                $$
                begin
                --  /*
                {trigger_body}
                --  */
                end
                $$
                language 'plpgsql';

                create trigger {trigger_name} {trigger_place} on {table_name}
                  for each row execute procedure trf_{trigger_name}()
                ;
                """
            trigger_block = self.unident(trigger_template).format(
                trigger_name=trigger.name,
                trigger_place=trigger.place,
                table_name=trigger.table,
                trigger_body='\n'.join(map(lambda body_line: '--  ' + body_line, trigger.body))
            )
            ddl_triggers.append(trigger_block)

        for data in self.schema.data[:]:
            data_line = re.sub("'now'", 'current_timestamp', data, flags=re.I)
            # print(data_line)
            sql_data.append(data_line)

        if not self.schema.host:
            self.schema.host = '127.0.0.1'

        prescript_template = """
            -- {file_encoding}
            set client_encoding to '{client_encoding}';

            -- connect to tcp:postgresql://{db_host}:5432/{master} user {db_user} identified by {db_password};
            -- drop database {db_alias};
            -- disconnect;
            -- create database {db_alias};

            -- connect to tcp:postgresql://{db_host}:5432/{db_alias} user {db_user} identified by {db_password};
            """

        file_encoding_utf8 = 'utf-8'
        file_encoding_win1251 = 'cp1251'
        pgsql_encoding_utf8 = 'UTF8'
        pgsql_encoding_win1251 = 'WIN1251'
        pg_encoding = {
            file_encoding_utf8: pgsql_encoding_utf8,
            file_encoding_win1251: pgsql_encoding_win1251
        }
        file_encoding = file_encoding_win1251
        pgsql_encoding = pg_encoding[file_encoding]

        prescript = self.unident(prescript_template).format(
            file_encoding=file_encoding,
            client_encoding=pgsql_encoding,
            master='postgres',  # may be 'template1'
            db_host=self.schema.host,
            db_user='postgres',
            db_password=self.schema.password,
            db_alias=self.schema.alias,
        )

        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        filename_pair = path.splitext(filename)
        filename_file = filename_pair[0]
        filename_ext = filename_pair[1]

        fn_main = filename
        fn_triggers = filename_file + '-triggers' + filename_ext
        fn_data = filename_file + '-data' + filename_ext
        fn_sp_template = '{0}-sp-{{stored_procedure_name}}.sql'.format(filename_file, filename_ext)
        fn_batch = filename_file + '.cmd'

        file_lines = []
        crlf = '\n'
        file_lines.append(prescript)
        file_lines.extend(sorted(ddl_sequences))
        file_lines.append(crlf)
        file_lines.extend(sorted(ddl_domains))
        file_lines.append(crlf)
        file_lines.extend(sorted(ddl_tables))
        file_lines.append(crlf)
        file_lines.extend(sorted(ddl_indices))
        file_lines.append(crlf)
        file_lines.extend(sorted(ddl_uk))
        file_lines.append(crlf)
        file_lines.extend(sorted(ddl_pk))
        file_lines.append(crlf)
        file_lines.extend(sorted(ddl_fk))
        file_lines.append(crlf)
        file_lines.extend(sorted(ddl_views))
                          
        f = codecs.open(fn_main, 'w', encoding=file_encoding)
        try:
            for file_line in file_lines:
                value = self.ugly_patch_replace_offset(file_line)
                f.write(value + '\n')
            f.write('/* EOF */\n')
        finally:
            f.close()

        #
        tr_filename = filename_file + '-triggers' + filename_ext

        if os.path.isfile(tr_filename):
            tr_filename += '~'
        if os.path.isfile(tr_filename):
            os.remove(tr_filename)

        f = open(tr_filename, 'w')
        try:
            f.write('\n'.join(sorted(ddl_triggers[:])))
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
            for data_item in sql_data[:]:
                f.write(data_item + '\n')
            f.write('/* EOF */\n')
        finally:
            f.close()

        # # #
        # # #
        # # #
        batch_template = """
            @echo off
            rem
            rem {file_encoding}
            rem

            cls

            set PATH=%PATH%;C:\\Program Files\\PostgreSQL\\9.1\\bin
            rem set HOME=C:\\home\\ark
            rem set PATH=%PATH%;%HOME%\\bin\\pgAdmin III 1.20.0

            rem set PGOPTIONS=--client-min-messages=warning
            rem # [i] debug w/echo: -e
            rem # [w] Don't use &PGHOST & $PGUSER variables here: -h %PGHOST% -U %PGUSER% -n -v ON_ERROR_STOP=1
            rem set PGPSQL_OPTS=-n -v ON_ERROR_STOP=1 -q
            set PGPSQL_OPTS=-v ON_ERROR_STOP=1

            set PGPSQL_EXE="psql.exe"
            set PGPSQL=%PGPSQL_EXE% %PGPSQL_OPTS%

            set PGCLIENTENCODING=utf-8
            rem set PGCLIENTENCODING=WIN
            rem set PGCLIENTENCODING=WIN1251

            set PGHOST={db_host}
            set PGHOSTADDR={db_host}
            set PGUSER={db_user}
            set PGPASSWORD={db_password}

            set DB414={db_alias}

            %PGPSQL% -d postgres -c "drop database %DB414%"
            %PGPSQL% -d postgres -c "create database %DB414%"
            %PGPSQL% -d %DB414% -c "create language 'plpgsql'"
            %PGPSQL% -d %DB414% -f {script_name_main}
            {script_procedure}
            %PGPSQL% -d %DB414% -f {script_name_triggers}
            rem %PGPSQL% -d %DB414% -f {script_name_data}

            echo "FIN: 9.1/4.1.8 %PGHOST%::%DB414%"
            pause

            rem echo "OK"
            pause
            """

        f = codecs.open(fn_batch, 'w', encoding=file_encoding)
        try:
            procedure_block = []
            for procedure_name in ddl_stored_procedures:
                procedure_block.append(
                    "%PGPSQL% -d %DB414% -f {sqlscript}".format(
                        sqlscript=path.basename(fn_sp_template.format(stored_procedure_name=procedure_name))
                    )
                )

            f.write(
                self.unident(batch_template).format(
                    file_encoding=file_encoding,
                    db_host=self.schema.host,
                    db_user='postgres',
                    db_password=self.schema.password,
                    db_alias=self.schema.alias,
                    script_name_main=path.basename(fn_main),
                    script_name_triggers=path.basename(fn_triggers),
                    script_name_data=path.basename(fn_data),
                    script_procedure='\n'.join(procedure_block)
                )
            )
        finally:
            f.close()





#
#
#
#COMMENT ON DATABASE comment_test
#  IS '123 dcefeorm
#
#
#qedf
#
#qwdf';
#
#
# COMMENT ON TABLE t1
#  IS 't1 comment
#multiline';
#
#COMMENT ON COLUMN t1.qw IS 'wwww';
#
# ##

  #
  # # 3) Create foreign keys (references)

  #
