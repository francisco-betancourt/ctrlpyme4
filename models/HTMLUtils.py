# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def data_table(headers=[], rows=[], fields=[]):
    """ Creates a data table with multiselect via checkboxes

        headers: the table headers
        rows: the set of rows obtained from db
        fields: the fields of the row that will be placed as table data, a field can be a string or a list, when the field is a list, all the list fields will be placed as a single column.
    """

    # the master checkbox
    thead = TH(INPUT(_type='checkbox', _id='master_checkbox'))
    for header in headers:
        thead.append(TH(header))
    thead = THEAD(thead)
    tbody = TBODY()
    for row in rows:
        # per row checkbox
        tr = TH(INPUT(_type='checkbox', _class='row_checkbox', _value=row.id), _scope='row')
        for field in fields:
            td = ''
            # if the field is a list, we iterate over its elements to concatenate the the row fields into a  single column
            if type(field) == type([]):
                for inner_field in field:
                    td += row[inner_field] + ' '
            else:
                td = row[field]
            tr.append(TD(td))
        tbody.append(tr)
    table = TABLE(thead, tbody, _class="table table-hover")
    table = DIV(table, _class="table_responsive") # responsiveness

    return table
