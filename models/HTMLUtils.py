# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


def option_btn(icon_name, action_url=None, action_name='', onclick=None):
    click_action = onclick if onclick else 'window.location.href = "%s"' % action_url
    button = BUTTON(I(_class='fa fa-%s' % icon_name), T(action_name), _type='button', _class='btn btn-default', _onclick=click_action)
    return button


def data_row(row, fields=[], deletable=True, editable=True, extra_options=[], controller=None, _vars={}, selectable=True):
    """ """
    options_enabled = deletable or editable or extra_options

    if not controller:
        controller = request.controller

    # per row checkbox
    tr = TH()
    if selectable:
        tr.append(INPUT(_type='checkbox', _class='row_checkbox', _value=row.id))
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
        vars_string = URL(vars=_vars).split('?')[1] if _vars else ''
        options_td = TD()
        if editable:
            options_td.append(option_btn('pencil', URL(controller, 'update', args=row.id, vars=_vars)))
        if deletable:
            delete_action = 'delete_rows("/%s", "", "%s")' % (row.id, vars_string)
            options_td.append(option_btn('trash', onclick=delete_action))
        # options must be related to the row, for that reason this function only allows same controller urls, and also it asumes that the first argument in the specified action is the row id.
        if extra_options:
            for option in extra_options:
                icon_name = option['icon_name'] if option.has_key('icon_name') else ''
                url_action = option['url_action'] if option.has_key('url_action') else None
                onclick = option['onclick'] if option.has_key('onclick') else None
                url_args=option['url_args'] if option.has_key('url_args') else []
                url_args.insert(0, row.id)
                url = URL(controller, url_action, args=url_args, vars=_vars)

                option_name = option['name'] if option.has_key('name') else ''

                options_td.append(option_btn(icon_name, url, option_name, onclick))
        tr.append(options_td)

        return tr


def data_headers(headers=[], options_enabled=True, selectable=True):
    # the master checkbox
    thead = TH()
    if selectable:
        thead.append(INPUT(_type='checkbox', _id='master_checkbox'))
    for header in headers:
        thead.append(TH(T(header)))
    if options_enabled:
        thead.append(TH(T('Options')))

    return thead


def data_table(head_cols, rows):
    pass


def data_table(headers=[], rows=[], fields=[], deletable=True,
               editable=True, extra_options=[], controller='', _vars={},
               selectable=True):
    """ Creates a data table with multiselect via checkboxes

        headers: the table headers
        rows: the set of rows obtained from db
        fields: the fields of the row that will be placed as table data, a field can be a string or a list, when the field is a list, all the list fields will be placed as a single column.
    """

    options_enabled = deletable or editable or extra_options

    # the master checkbox
    thead = data_headers(headers=headers, options_enabled=options_enabled, selectable=selectable)
    thead = THEAD(thead)
    tbody = TBODY()
    for row in rows:
        tr = data_row(row, fields=fields, deletable=deletable, editable=editable, extra_options=extra_options, controller=controller, _vars=_vars, selectable=selectable)
        tbody.append(tr)
    table = TABLE(thead, tbody, _class="table table-hover")
    table = DIV(table, _class="table-responsive") # responsiveness

    return table
