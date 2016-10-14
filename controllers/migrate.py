# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bet@net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Author Francisco Betancourt <francisco@betanetweb.com>


expiration_redirect()


def index():
    allow_import_table=['brand','category','measure_unit','item','supplier','payment_opt']
    btn_class_tables=['label','format_indent_increase','','shopping_basket','','']
    migration_tables=db(db.migration_table).select()
    already_uploaded=[row.table_name for row in migration_tables]
    return dict(allow_import_table=allow_import_table,btn_class_tables=btn_class_tables,
        already_uploaded=already_uploaded)

def migrate_table():
    null_strings=['','NULL','null','<NULL>','<null>']
    if not request.vars.table_name or not db.get(request.vars.table_name):
        raise HTTP(404)
    #If a csv_file is present means you already uploaded now you want to configure the import
    if request.vars.csv_file and request.vars.table_id:
        try:
            csv_file=open(request.folder+'/static/migrations/'+request.vars.csv_file,'r')
            columns=csv_file.readline().split(",")
        except:
            session.flash=T('An error ocurred while reading the file')
            redirect(URL('migrate_table',vars={'table_name':request.vars.table_name}))
        table_id_replace_select=SELECT(OPTION(T('Select table to replace id'),_value="-1"),_class="form-control")
        migration_tables=db(db.migration_table).select()
        i=0
        for t in migration_tables:
            table_id_replace_select.append(OPTION(t.table_name,_value=t.id))
        columns_select=SELECT(OPTION(T('Select the field that matches this column if available'),_value=-1),_class="form-control")
        i=0
        for c in columns:
            columns_select.append(OPTION(c,_value=i))
            i+=1
        column_match_form=FORM(_class="form-horizontal")
        from copy import deepcopy
        for f in db[request.vars.table_name].fields:
            row_select=deepcopy(columns_select)
            row_select['_name']='map_'+f
            table_row_select=deepcopy(table_id_replace_select)
            table_row_select['_name']='idrep_'+f
            if f!='id':
                column_match_form.append(DIV(LABEL(db[request.vars.table_name][f].label,_class="control-label"),
                row_select,table_row_select,_class="form-group"
                ))
        #column_match_form.append(INPUT(_type="hidden", _name="table_name", _value=request.vars.table_name))
        column_match_form.append(DIV(INPUT(_value=T("Submit"),_type="submit",_class="btn btn-primary btn-default"),_class="form-group"))
        #ToDo add form check box to control id tracking and replacing
        #column_match_form.append(DIV(LABEL(T('Track and replace old ids'))))
        #Lets build a dictionary of columns to match
        match_dictionary={}
        replace_dictionary={}
        replace_dictionary_at_end={}
        if column_match_form.validate():
            for k,v in column_match_form.vars.iteritems():
                if k[:4]=='map_' and v!='-1' and v!=-1:
                    match_dictionary[k[4:]]=int(v)
                elif k[:6]=='idrep_' and v!='-1' and v!=-1:
                    replace_dictionary[k[6:]]=int(v)
            #Now lets read all values and insert keeping old ids!
            if len(match_dictionary)>0:
                import csv
                csv_reader=csv.reader(csv_file)
                insert_data=[]
                old_id_data=[]
                old_ids=[]
                for data in csv_reader:
                    #Create the row data
                    row_data={k:(data[v] if data[v] not in null_strings else None) for k,v in match_dictionary.iteritems()}
                    #Replace selected fields
                    for k,v in replace_dictionary.iteritems():
                        replace_id=db((db.migration_dictionary.id_migration_table==v)&(db.migration_dictionary.old_id==row_data[k])).select().first()
                        if replace_id:
                            row_data[k]=replace_id.new_id
                    #Insert row with replaced fields
                    new_id=db[request.vars.table_name].insert(**row_data)
                    db.migration_dictionary.insert(id_migration_table=request.vars.table_id,old_id=data[0],new_id=new_id)

                    #insert_data.append({k:(data[v] if data[v] not in null_strings else None) for k,v in match_dictionary.iteritems()})
                    #for k,v in replace_dictionary.iteritems():
                    #    insert_data[-1][k]=db((db.migration_dictionary.id_migration_table==v)&(db.migration_dictionary.old_id==insert_data[-1][k])).select().first().new_id
                    #old_ids.append(data[0])
                    #if len(insert_data)>1000:
                    #    inserted_ids=db[request.vars.table_name].bulk_insert(insert_data)
                    #    old_id_data=[{'id_migration_table':request.vars_table_id,'old_id':old_ids[i],'new_id':inserted_ids[i]} for i in range(len(insert_data)) ]
                    #    db.migration_dictionary.bulk_insert(old_id_data)
                    #    insert_data=[]
                    #    old_id_data=[]
                #if len(insert_data)>0:
                #    inserted_ids=db[request.vars.table_name].bulk_insert(insert_data)
                #    old_id_data=[{'id_migration_table':request.vars.table_id,'old_id':old_ids[i],'new_id':inserted_ids[i]} for i in range(len(insert_data)) ]
                #    db.migration_dictionary.bulk_insert(old_id_data)
                #Now if replacing from this table do it now
                #for k,v in replace_dictionary_at_end.iteritems():
                #    rows_to_replace=db(db[request.vars.table_name][k]!=None).select(db[request.vars.table_name][k])
                #    for row in rows_to_replace:
                #        new_id=db((db.migration_dictionary.id_migration_table==v)&(db.migration_dictionary.old_id==insert_data[-1][k])).select().first().new_id
                #        row.update_record({k:new_id})
                session.flash=request.vars.table_name+' '+T('migrated correctly')
                redirect(URL('migrate','index'))
        response.flash=T('Files processed correctly')
        return dict(form=column_match_form)
    else:
        db.migration_table.table_name.default=request.vars.table_name
        form=SQLFORM(db.migration_table)
        if form.process().accepted:
            redirect(URL('migrate_table',vars={'table_name':request.vars.table_name,'csv_file':form.vars.csv_file,'table_id':form.vars.id}))
    return dict(form=form)
