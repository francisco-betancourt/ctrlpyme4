# -*- coding: utf-8 -*-
# The MIT License (MIT)
# Copyright (c) 2016 Daniel J. Ramirez
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from gluon.storage import Storage
# from gluon.html import *
# from gluon import current, URL
# from html_utils import ICON, pages_menu_bare

t_index = 0


def OPTION_BTN(icon_name='', url='#', text='', _onclick='', title=''):
    if _onclick:
        return A(ICON(icon_name), text, _onclick=_onclick, _title=title)
    else:
        return A(ICON(icon_name), text, _href=url, _title=title)


def supert_default_options(row):
    T = current.T

    request = current.request
    update_btn = OPTION_BTN('edit', URL(request.controller, 'update', args=row.id), title=T('edit'))
    hide_btn = OPTION_BTN('visibility_off', _onclick='delete_rows("/%s", "", "show_hidden=%s")' % (row.id, request.vars.show_hidden), title=T('hide'))
    try:
        # unhide button if the item is not active
        if not row.is_active:
            hide_btn = OPTION_BTN('visibility', URL("undelete", args=row.id, vars=dict(show_hidden=request.vars.show_hidden)), title=T('unhide'))
    except:
        pass
    return update_btn, hide_btn


def row_data_from_field(row, field):
    keys = field.split('.')
    data = row
    for key in keys:
        data = data[key]
        if not data:
            break
    return data


def base_multifield_format(row, subfields):
    data = ''
    for sub_field in subfields:
        data += '%s ' % row_data_from_field(row, sub_field)
    return data


def _search_query(field, term):
    join = None
    db = current.db
    splited_field = field.split('.')
    table_name, field = splited_field[0], splited_field[1]

    try:
        field_type, ref_table = db[table_name][field].type.split(' ')[:2]
        is_reference = field_type == 'reference'
        if is_reference:
            join = db[table_name][field] == db[ref_table].id
    except:
        pass

    if join and len(splited_field) > 2:
        joined_table_field = splited_field[2]
        if db[ref_table][joined_table_field].type == 'string':
            return join & db[ref_table][joined_table_field].contains(term)
        if db[ref_table][joined_table_field].type == 'integer':
            try:
                return join & db[ref_table][joined_table_field] == int(term)
            except:
                pass

    # this is for not joined field
    if db[table_name][field].type == 'string':
        return db[table_name][field].contains(term)
    if db[table_name][field].type == 'integer':
        try:
            return db[table_name][field] == int(term)
        except:
            pass
    else:
        return None


def search_query_from_field(field, term):
    q = None
    for subfield in field:
        if not q:
            q = _search_query(subfield, term)
        else:
            s = _search_query(subfield, term)
            if s:
                q |= s
    return q


def parse_field(field, base_table_name, joined=False, search_term=None):
    """ Parses field data into an intermediate representation usable by data formaters, the returned object is

        field:
        header: the header for the specified field
        orderby: string that can be used to sort the table by the field
        search: a search query for the specified field
        format: The format function that will be applied to the specified field
    """

    db = current.db
    header = None
    new_field = ''
    orderby = '%s.%s' % (base_table_name, field) if not joined else str(field)
    func = row_data_from_field
    if type(field) == dict:
        field = Storage(field)
        # we only accept an array of subfields
        if not field.fields or type(field.fields) != list:
            raise ValueError('No fields key found or fields is not list')
        # this is just in case the user does not define a label for the joined fields
        joined_field_names = ' '.join(field.fields) if joined else ' '.join(map(lambda field : base_table_name + '.' + field, field.fields))
        data_format = field.custom_format if field.custom_format else base_multifield_format
        new_field = field.fields
        func = data_format
        header = field.label_as if field.label_as else joined_field_names
        # set the orderby string to be the specified table and fields
        joined_field_names = joined_field_names.replace(' ', '+')
        orderby = '%s' % (joined_field_names)
    else:
        if joined:
            table_name, field_name = field.split('.')
            header = db[table_name][field_name].label
        else:
            header = db[base_table_name][field.split('.')[0]].label
        new_field = field
    s_q = search_query_from_field(orderby.split('+'), search_term) if search_term else None
    return Storage({
        'field': new_field,
        'header': header,
        'orderby': orderby,
        'search': s_q,
        'format': func
    })



def sort_header(field, t_index=0):
    request = current.request

    orderby_key = 'orderby_%s' % t_index
    order_key = 'order_%s' % t_index
    new_vars = Storage(request.vars)
    content = field.header
    orderby = request.vars[orderby_key]
    ascendant = request.vars[order_key] == 'asc'
    icon = ''
    classes = ''
    if orderby == field.orderby:
        content = B(field.header)
        icon_name = 'arrow_upward' if ascendant else 'arrow_downward'
        icon = ICON(icon_name, _class='st-header-icon')
        classes = 'selected'
        ascendant = not ascendant
    else:
        ascendant = True
    new_vars[order_key] = 'asc' if ascendant else 'dsc'
    new_vars[orderby_key] = field.orderby
    url = URL(request.controller, request.function, args=request.args, vars=new_vars)
    return icon, A(content, _href=url, _class='st-header ' + classes)


def SUPERT_BARE(query, select_fields=None, select_args={}, fields=[], ids=[], search_term=None, base_table_name=None, include_row=False):
    """
    about fields, fields is an array of <value> where every <value> is either
    a dict or a string.

    if the <value> is string, then for every row this function will get
    row['<value>'] and use the header db[<default table>][field].label, subfields can be specified using dot notation

    if the <value> is a dict, then we can specify the following parameters:
        fields: []
        label_as: name of the grouped fields
        custom_format: function applied to every row fields group
        example:
        {
           'fields': ['somefield', 'somefield.innerfield'],
           'label_as': 'Label',
           'custom_format': lambda row, fields: "%s" % row.field)
        }
    using a dict will group the specified fields into a single one.
    """
    db = current.db

    # this query is used to get table or tables name(s), since this value is not specified, and only a query is given
    rows = None
    copy_select_args = select_args.copy() if select_args else dict()
    copy_select_args['limitby'] = (0,1)
    if select_fields:
        rows = db(query).select(*select_fields, **copy_select_args)
    else:
        rows = db(query).select(**copy_select_args)
    if not rows:
        return None, None

    joined = False # true if the query contains joined data
    if base_table_name:
        # in case of joined tabled, the user need to specify the main table
        joined = type(rows.first()) == type(rows.first()[base_table_name])
    if not joined:
        # if not joined we infer the table name using the result
        base_table_name = rows.colnames[0].split('.')[0]
        #if not select_fields:
        #    select_fields = [db[base_table_name].ALL]

    # default order, newest first
    if not select_args.has_key('orderby'):
        select_args['orderby'] = ~db[base_table_name].id

    # only selected records
    ids_query = None
    for _id in ids:
        try:
            _id = int(_id)
            if not ids_query:
                ids_query = db[base_table_name].id == _id
            else:
                ids_query |= db[base_table_name].id == _id
        except:
            pass
    if ids_query:
        query &= ids_query

    # normalize fields
    search_query = None
    datas = []
    new_fields = []
    for field in fields:
        new_field = parse_field(field, base_table_name, joined, search_term)
        new_fields.append(new_field)
        if new_field.search:
            if not search_query:
                search_query = new_field.search
            else:
                search_query |= new_field.search
    if search_query:
        query = query & search_query

    if select_fields:
        rows = db(query).select(*select_fields, **select_args)
    else:
        rows = db(query).select(**select_args)

    for row in rows:
        row_id = None

        # something happened to the query and its returning something like a join
        _row = row
        try:
            if not joined:
                _row = row[base_table_name]
        except:
            pass

        if not joined:
            row_id = _row['id']
        else:
            row_id = _row[base_table_name].id
        values = []
        for field in new_fields:
            values.append(field.format(_row, field.field))
        datas.append(Storage(_id=row_id, _values=values, _row=_row))

    global t_index
    t_index += 1

    return new_fields, datas


def visibility_g_option():
    new_vars = Storage(request.vars.copy())
    if new_vars.show_hidden == 'yes':
        del new_vars.show_hidden
        text = T("don't show hidden")
    else:
        new_vars.show_hidden = 'yes'
        text = T("show hidden")

    url = URL(request.controller, request.function, args=request.args, vars=new_vars)
    return (text, url)



def supert_table_format(fields, datas, prev_url, next_url, ipp, searchable=False, selectable=False, options_enabled=False, options_func=supert_default_options, global_options=[], title='', page=None, pages_count=None, t_index=0):

    T = current.T

    # base_table
    table = DIV(_class="st-content")
    if datas and fields:
        for index, field in enumerate(fields):
            container = DIV(_class="st-col")
            head = sort_header(field, t_index)
            container.append(DIV(head, _class="st-row-data st-last top"))
            for data in datas:
                current_data = data._values[index]
                # say localized YES or NO instead of True False
                if type(current_data) == bool:
                    current_data = T('yes') if current_data else T('no')
                if current_data is None or type(current_data) == str and current_data.strip() == 'None':
                    current_data = ''
                container.append(
                    DIV(current_data, _class="st-row-data st-row-%s" % data._id)
                )
            table.append(container)
    else:
        container = DIV(_class="st-col")
        contents = T('No records found')
        if global_options:
            contents += T('try showing hidden records using') + ': '
            contents = (contents, ICON('more_vert'))
        container.append(DIV(contents , _class="st-row-data"))
        table.append(container)

    t_header = ''
    t_header = DIV(_class="st-row-data top st-card-header", _id="supert_card_header");
    t_header_content = DIV(_class="st-card-header-content")
    # add search field
    if title:
        t_header_content.append(H4(title))
    if searchable:
        search_form = FORM(_class="form-inline st-search-form")
        search_form.append(
            INPUT(_class="form-control st-search-input", _name='supert_search')
        )
        search_form.append(
            BUTTON(ICON('search'), _class="btn btn-default st-search-form-btn")
        )
        t_header_content.append(search_form)
    if global_options:
        options_ul = UL(_class='dropdown-menu')
        for option in global_options:
            title, url = option
            options_ul.append(LI(A(title, _href=url)))
        g_options = DIV(
            BUTTON(ICON('more_vert'), _class='st-g-options-btn', _type='button', data={'toggle': "dropdown"}), options_ul,
            _class="dropdown supert-global-options"
        )
        t_header_content.append(g_options)
    if selectable:
        selected_options = DIV(_class='st-card-header-options')
        checks = DIV(_class="st-col st-checks-col")
        checks.append(DIV(CB(_id="cb_master"), _class="st-row-data st-last top st-options st-header st-check"))
        for data in datas:
            checks.append(DIV(CB(_id="cb_%s" % data._id), _class='st-row-data st-option st-check'))
        table.insert(0, checks)
    t_header.append(t_header_content)

    # add options
    if options_enabled:
        options = DIV(_class="st-col")
        options.append(DIV(T('Options'), _class="st-row-data st-last top st-options st-header"))
        for data in datas:
            options.append(DIV(options_func(data._row), _class='st-row-data st-option st-row-%s' % data._id))
        table.append(options)
    t_footer = DIV(_class="st-row-data st-last bottom st-footer")
    t_footer.append(DIV(T('Items per page'), _class='st-footer-element'))
    t_footer.append(DIV(
        SPAN(ipp, _class="ipp-value"),
        FORM(
            INPUT(_value=ipp, _class="form-control", _name='supert_search'),
            _class="form-inline st-ipp-form", _hidden=True
        )
        , _class="st-ipp"
    ))
    if page >= 0:
        t_footer.append(DIV(T('Page'), _class='st-footer-element'))
        t_footer.append(DIV(page + 1, _class="st-ipp"))
    t_footer.append(A(ICON('keyboard_arrow_left'), _class='st-prev-page', _href=prev_url))
    t_footer.append(A(ICON('keyboard_arrow_right'), _class='st-next-page', _href=next_url))

    table = DIV(t_header, table, t_footer, _class="supert table-responsive", _id="supert_%s" % t_index, **{'_data-index': t_index})

    return table



def SUPERT(query, select_fields=None, select_args={}, fields=[], options_func=supert_default_options, options_enabled=True, selectable=False, searchable=True, base_table_name=None, title='', global_options=[visibility_g_option()]):
    """ default supert with table output. recognized url parameters:
        term: search term
        orderby: field or fields to orderby, it can be something like items.price+items.barcode
        order: asc if the order will be ascendant, descendant in other case
        page: since results are paged this parameter determines the current page
        ipp: the number of items per page
        ids: list of comma separated ids to apply the table to a subset of items
    """
    global t_index
    current_t_index = t_index

    request = current.request
    db = current.db

    specified_base_table_name = base_table_name
    # normalize fields
    search_term = request.vars['term_%s' % t_index]
    # ordering
    if request.vars['orderby_%s' % t_index]:
        orderby = None
        for f_string in request.vars['orderby_%s' % t_index].split('+'):
            tname, f_name = f_string.split('.')
            orderparam = db[tname][f_name] if request.vars['order_%s' % t_index] == 'asc' else ~db[tname][f_name]
            if not orderby:
                orderby = orderparam
            else:
                orderby |= orderparam
        select_args['orderby'] = orderby
    # limits
    distinct = db[base_table_name].id if base_table_name else None
    page = request.vars['page_%s' % t_index]
    ipp = request.vars['ipp_%s' % t_index]
    try:
        page = int(page or 0)
        ipp = int(ipp or 10)
    except:
        page = 0
        ipp = 10
    prev_url, next_url, limits, pages_count  = pages_menu_bare(query, page, ipp, distinct=distinct, index=t_index)
    select_args['limitby'] = limits

    ids = request.vars['ids_%s' % t_index]
    ids = ids.split(',') if ids else []

    new_fields, datas = SUPERT_BARE(query, select_fields, select_args, fields, ids, search_term, base_table_name, include_row=True)

    if not datas:
        datas = []

    # base_table
    table = supert_table_format(new_fields, datas, prev_url, next_url, ipp, searchable=searchable, selectable=selectable, options_enabled=options_enabled, options_func=options_func, global_options=global_options, title=title, t_index=current_t_index, page=page, pages_count=pages_count)

    return table
