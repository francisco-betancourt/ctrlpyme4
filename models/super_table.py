from gluon.storage import Storage


def OPTION_BTN(icon_name='', url='#', text='', _onclick=''):
    if _onclick:
        return A(ICON(icon_name), text, _onclick=_onclick)
    else:
        return A(ICON(icon_name), text, _href=url)


def supert_default_options(row):
    update_btn = OPTION_BTN('edit', URL(request.controller, 'update', args=row.id))
    hide_btn = OPTION_BTN('visibility_off', _onclick='delete_rows("/%s", "", "")' % (row.id))
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


def parse_field(field, row, base_table_name, joined=False):
    header = None
    data = ''
    orderby = '%s.%s' % (base_table_name, field) if not joined else str(field)
    if type(field) == dict:
        field = Storage(field)
        # we only accept an array of subfields
        if not field.fields or type(field.fields) != list:
            raise ValueError('No fields key found or fields is not list')
        # this is just in case the user does not define a label for the joined fields
        joined_field_names = ' '.join(field.fields) if joined else ' '.join(map(lambda field : base_table_name + '.' + field, field.fields))
        data_format = field.custom_format if field.custom_format else base_multifield_format
        data = data_format(row, field.fields)
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
        data = row_data_from_field(row, field)
    return header, data, orderby


def sort_header(header):
    new_vars = Storage(request.vars)
    content = header.value
    orderby = request.vars.orderby
    ascendant = request.vars.order == 'asc'
    icon = ''
    classes = ''
    if orderby == header.orderby:
        content = B(header.value)
        icon_name = 'arrow_upward' if ascendant else 'arrow_downward'
        icon = ICON(icon_name, _class='st-header-icon')
        classes = 'selected'
        ascendant = not ascendant
    else:
        ascendant = True
    new_vars.order = 'asc' if ascendant else 'dsc'
    new_vars.orderby = header.orderby
    url = URL(request.controller, request.function, args=request.args, vars=new_vars)
    return icon, A(content, _href=url, _class='st-header ' + classes)


def SUPERT(query, select_fields=None, select_args={}, fields=[], options_func=supert_default_options, options_enabled=True, selectable=False, searchable=True, base_table_name=None):
    """
    about fields, fields is an array of <value> where every <value> is either
    a dict or a string.

    if the <value> is string, then for every row this function will get
    row['<value>'] and use the header db[<default table>][field].label

    if the <value> is a dict, then we can specify the following parameters:
        fields: []

        label_as:

    """

    # ordering
    try:
        orderby = None
        for f_string in request.vars.orderby.split('+'):
            tname, f_name = f_string.split('.')
            orderparam = db[tname][f_name] if request.vars.order == 'asc' else ~db[tname][f_name]
            if not orderby:
                orderby = orderparam
            else:
                orderby |= orderparam
        select_args['orderby'] = orderby
    except:
        import traceback as tb
        tb.print_exc()
        # pass

    # limits
    distinct = db[base_table_name].id if base_table_name else None
    page = request.vars.page
    ipp = request.vars.ipp
    try:
        page = int(page or 0)
        ipp = int(ipp or 10)
    except:
        page = 0
        ipp = 10
    prev_url, next_url, limits, pages_count  = pages_menu_bare(query, page, ipp, distinct=distinct)
    select_args['limitby'] = limits

    rows = None
    try:
        rows = db(query).select(select_fields, **select_args)
    except:
        rows = db(query).select(**select_args)

    if not rows:
        return None

    headers = []
    # for every header there will be one sub array so we will have a matrix where every row is like a column asociated with the header at the same index
    datas = []
    # we use this base name, when we dont have joins so we can get the table field labels
    joined = False
    if base_table_name:
        joined = type(rows.first()) == type(rows.first()[base_table_name])
    if not joined:
        base_table_name = rows.colnames[0].split('.')[0]
    headers_added = False
    for row in rows:
        for index, field in enumerate(fields):
            header, data, orderby = parse_field(field, row, base_table_name, joined)
            # initialize data arrays if the haven't been initialized
            if not headers_added:
                headers.append(Storage(value=header, orderby=orderby))
                datas.append([])
            datas[index].append(data)
        headers_added = True

    # output format
    table = DIV(_class="st-content")
    for index, header in enumerate(headers):
        container = DIV(_class="st-col")
        head = sort_header(header)
        container.append(DIV(head, _class="st-row-data st-last top"))
        for data in datas[index]:
            container.append(DIV(data, _class="st-row-data"))
        table.append(container)

    t_header = ''
    t_header = DIV(_class="st-row-data top st-card-header", _id="supert_card_header");
    t_header_content = DIV(_class="st-card-header-content")
    if searchable:
        search_form = FORM(_id='supert_search_form', _class="form-inline")
        search_form.append(INPUT(_class="form-control", _name='supert_search', _id='supert_search'))
        search_form.append(BUTTON(ICON('search'), _class="btn btn-default", _id="supert_search_btn"))
        t_header_content.append(search_form)
    if selectable:
        selected_options = DIV(_class='st-card-header-options', _id='st_card_header_options')
        checks = DIV(_class="st-col st-checks-col")
        checks.append(DIV(CB(_id="cb_master"), _class="st-row-data st-last top st-options st-header st-check"))
        for row in rows:
            row_id = row.id if not joined else row[base_table_name].id
            checks.append(DIV(CB(_id="cb_%s" % row_id), _class='st-row-data st-option st-check'))
        table.insert(0, checks)
    t_header.append(t_header_content)

    # add options
    if options_enabled:
        options = DIV(_class="st-col")
        options.append(DIV(T('Options'), _class="st-row-data st-last top st-options st-header"))
        for row in rows:
            row = row[base_table_name] if joined else row
            options.append(DIV(options_func(row), _class='st-row-data st-option'))
        table.append(options)
    t_footer = DIV(_class="st-row-data st-last bottom st-footer")
    t_footer.append(DIV(T('Items per page')))
    t_footer.append(DIV(ipp, _class="st-ipp"))
    t_footer.append(A(ICON('keyboard_arrow_left'), _class='st-prev-page', _href=prev_url))
    t_footer.append(A(ICON('keyboard_arrow_right'), _class='st-next-page', _href=next_url))

    table = DIV(t_header, table, t_footer, _class="supert")

    return table
