#!/usr/bin/env python
#!/usr/bin/python

import re
import os
import ibe_ddl

from os import path


# PYSDUN - PYthon Schema/structure of Database UNificator
# Convert IbeSchema to PostgreSQL script
class PysdunPgsql:

    def __init__(self, schema):
        self.schema = schema

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
        # [!] don't do it w/o huge testing: result = re.sub("[\s+\.]offset[;\s+\,]", ' "offfset" ', result, re.IGNORECASE)
        return result

    @staticmethod
    def ugly_patch_replace_dvbservice_sequence(value):
        if value == 'dvbservice':
            return 'dvbservice_seq'
        return value

    @staticmethod
    def replace_data_type(data_type):
        blob_bin = 'text';  # [!] 'bytea'
        blob_memo = 'text';
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
        data_type = re.sub('datetime', 'timestamp', data_type, re.IGNORECASE)
        data_type = re.sub("'now'", 'current_timestamp', data_type, re.IGNORECASE)

        data_type = PysdunPgsql.ugly_patch_replace_binary(data_type)
        return data_type

    def export(self, filename):
        filename_pair = path.splitext(filename)
        filename_file = filename_pair[0]
        filename_ext = filename_pair[1]

        lines = []
        #
        sequences = set()
        for generator in self.schema.generators:
            sequence_name = generator.name
            sequence_name = PysdunPgsql.ugly_patch_replace_dvbservice_sequence(sequence_name)
            sequences.add(sequence_name)
        #
        for sequence in sequences:
            lines.append('create sequence {0}'.format(sequence))

        if self.schema.domains:
            for domain in self.schema.domains:
                data_type = PysdunPgsql.replace_data_type(domain.data_type)

                domain_name = domain.name
                domain_name = PysdunPgsql.ugly_patch_replace_binary(domain_name)
                lines.append('create domain {0} as {1}'.format(domain_name, data_type))
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
            template = 'create table {} ({})'
            table_statement = template.format(
                table.name,
                ', '.join([str(f) for f in field_list]))
            lines.append(table_statement)
        #
        for table_name in self.schema.tables:
            table = self.schema.tables[table_name]
            if table.uk is not None:
                for fk_name in table.uk:
                    field_list = table.uk[fk_name]
                    template = 'alter table {} add constraint {} unique ({})'
                    fk_statement = template.format(
                        table_name, fk_name,
                        ', '.join([str(f) for f in field_list]))
                    lines.append(fk_statement)
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
                    lines.append(index_statement)
            if table.pk is not None:
                pk_name = 'pk_{}'.format(table_name)
                template = 'alter table {} add constraint {} primary key ({})'
                pk_statement = template.format(
                    table_name, pk_name,
                    ', '.join([str(f) for f in table.pk]))
                lines.append(pk_statement)
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
                    lines.append(fk_statement)
        #
        for view in self.schema.views:
            lines.append(view)


        prescript = []
        prescript.append('-- connect to tcp:postgresql://192.168.47.134:5432/postgres user postgres identified by postgres')
        prescript.append('-- drop database pysdun');
        prescript.append('-- disconnect')
        prescript.append('-- create database pysdun;')
        prescript.append('-- connect to tcp:postgresql://192.168.47.134:5432/pysdun user postgres identified by postgres')
        prescript.append('-- connect to tcp:postgresql://127.0.0.1:5432/postgres user postgres identified by postgres')
        prescript.append('-- connect to tcp:postgresql://127.0.0.1:5432/postgres user postgres identified by masterkey')
        prescript.append('-- connect to tcp:postgresql://127.0.0.1:5432/dfpostdb user postgres identified by postgres')
        prescript.append('-- connect to tcp:postgresql://127.0.0.1:5432/dfpostdb user postgres identified by masterkey')

        f = open(filename, 'w')
        try:
            for item in prescript[:]:
                f.write(item + ';\n')
            for item in lines:
                value = item
                value = PysdunPgsql.ugly_patch_replace_offset(value)
                f.write(value + ';\n')
            # for item in ins:
            #     f.write(item + ';\n')
        finally:
            f.close()

        #
        #
        #
        #
        filename = filename_file + '-triggers' + filename_ext

        if os.path.isfile(filename):
            filename = filename + '~'
        if os.path.isfile(filename):
            os.remove(filename)

        lines = []

        for tr in self.schema.triggers:
            body_mark = '$body$'
            trigger_procedure = 'trf_{}'.format(tr.name)
            lines.append('/* - - - - - - - - - - - - - - - - */')
            lines.append('create or replace function {}()'.format(trigger_procedure))
            lines.append('  returns opaque as')
            lines.append(body_mark)
            lines.append('-- / *')

            for b in tr.body:
                lines.append('-- ' + b)

            lines.append('-- * /')
            lines.append(body_mark)
            lines.append("language 'plpgsql'")
            lines.append(';')

            lines.append('/* - - - - */')
            lines.append('create trigger {}'.format(tr.name))
            lines.append('{}'.format(tr.place))
            lines.append('on {}'.format(tr.table))
            lines.append('for each row execute procedure {}'.format(trigger_procedure))
            lines.append(';')

        f = open(filename, 'w')
        try:
            for item in prescript:
                f.write(item + ';\n')
            for item in lines:
                f.write(item + '\n')
            # for item in ins:
            #     f.write(item + ';\n')
        finally:
            f.close()


        #
        #
        #
        #
        filename = filename_file + '-proc' + filename_ext

        if os.path.isfile(filename):
            filename = filename + '~'
        if os.path.isfile(filename):
            os.remove(filename)

        lines = []

#   (
# freq frequency,
# begtime timestamp,
# endtime timestamp,
# immed boolean,
# breaked boolean,
# dfexist boolean,
# pfexist boolean,
# pwrexist boolean,
# sndexist boolean,
# spcexist boolean,
# alsexist boolean,
# dvbalsexist boolean,
# dvbt2alsexist boolean,
# closed boolean,
# ses_id guid,
# sysname shortname
#   )

        #
        # select * from freqsessproc(null, null, null, null)
        # union
        # select * from freqsessview
        for sp in self.schema.procedures:
            body_mark = '$body$'
            lines.append('/* - - - - - - - - - - - - - - - - */')
            lines.append('create or replace function {}'.format(sp.name))
            lines.append('-- returns table (col1 int, col2 text) ')
            lines.append('-- returns setof record ')
            lines.append('-- returns opaque ')
            lines.append('-- returns void ')
            lines.append('-- returns setof {}_view'.format(sp.name))
            lines.append('as')
            lines.append(body_mark)
            lines.append('--  declare')
            lines.append('--    r {}_view%rowtype;'.format(sp.name))
            lines.append('-- / *')

            for b in sp.body:
                lines.append('-- ' + b)

            lines.append('-- * /')
            lines.append(body_mark)

            lines.append("language 'plpgsql' immutable")
            # immutable --> STABLE
            lines.append(';')


        f = open(filename, 'w')
        try:
            for item in prescript:
                f.write(item + ';\n')
            for item in lines:
                f.write(item + '\n')
            # for item in ins:
            #     f.write(item + ';\n')
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
