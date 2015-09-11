# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


def option_btn(icon_name, action_url, action_name=''):
    button = BUTTON(SPAN(_class='glyphicon glyphicon-%s' % icon_name), action_name, _type='button', _class='btn btn-default', _onclick='window.location.href = "%s"' % action_url)
    return button


def data_table(headers=[], rows=[], fields=[], deletable=True,
               editable=True, extra_options=[]):
    """ Creates a data table with multiselect via checkboxes

        headers: the table headers
        rows: the set of rows obtained from db
        fields: the fields of the row that will be placed as table data, a field can be a string or a list, when the field is a list, all the list fields will be placed as a single column.
    """

    options_enabled = deletable or editable or extra_options

    # the master checkbox
    thead = TH(INPUT(_type='checkbox', _id='master_checkbox'))
    for header in headers:
        thead.append(TH(T(header)))
    if options_enabled:
        thead.append(TH(T('Options')))
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
        # Options
        if options_enabled:
            options_td = TD()
            if editable:
                options_td.append(option_btn('pencil', URL('update', args=row.id)))
            if deletable:
                options_td.append(option_btn('trash', URL('delete', args=row.id)))
            if extra_options:
                for option in extra_options:
                    icon_name = option['icon_name'] if option.has_key('icon_name') else ''
                    url = option['url'] if option.has_key('url') else '#'
                    option_name = option['name'] if option.has_key('name') else ''

                    options_td.append(option_btn(icon_name, url, option_name))
            tr.append(options_td)

        tbody.append(tr)
    table = TABLE(thead, tbody, _class="table table-hover")
    table = DIV(table, _class="table_responsive") # responsiveness

    return table
