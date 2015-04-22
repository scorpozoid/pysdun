#!/usr/bin/env python
#!/usr/bin/python

import ddl
import re


# PYSDUN - PYthon Schema/structure of Database UNificator
class PysdunPgsql:

    def __init__(self, schema):
        self.schema = schema

    @staticmethod
    def ugly_patch_replace_binary(value):
        return value.replace('binary', 't_binary')

    @staticmethod
    def replace_data_type(data_type):
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
                    '0': 'bytea',
                    '1': 'text'
                }
                if sub_type in sub_types:
                    data_type = sub_types[sub_type]
                else:
                    data_type = 'bytea'
        data_type = re.sub('datetime', 'timestamp', data_type, re.IGNORECASE)
        data_type = re.sub("'now'", 'current_timestamp', data_type, re.IGNORECASE)

        data_type = PysdunPgsql.ugly_patch_replace_binary(data_type)
        return data_type

    def export(self, filename):
        lines = []
        #
        for generator in self.schema.generators:
            lines.append('create sequence {0}'.format(generator.name))
        #

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
                            data_type = ''
                            #serial = 'serial'
                            serial = 'bigserial'
                            for generator in self.schema.generators:
                                if generator.is_ownered_by(table_name, field.name):
                                    serial = ''
                                    default = 'default nextval({})'.format(generator.name)
                                    break
                        break
                field_item = '{} {} {} {} {}'.format(field.name, serial, data_type, not_null, default)
                field_item = ddl.strip_statement(field_item)

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
                        table_name, field_list,
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
                    index_statement = ddl.strip_statement(index_statement)
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
                    fk_statement = ddl.strip_statement(fk_statement)
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
            for item in prescript:
                f.write(item + ';\n')
            for item in lines:
                f.write(item + ';\n')
            # for item in ins:
            #     f.write(item + ';\n')
        finally:
            f.close()


  #
  # # 3) Create foreign keys (references)

  #
