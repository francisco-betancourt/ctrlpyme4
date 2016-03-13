from gluon.storage import Storage

def create_sort_link(field):
    if type(field) == dict:
        request.vars.orderby = '_'.join(field['fields'])
        name = field['name']
    else:
        request.vars.orderby = field['name']
        name = field['name']
    sort_url = URL(request.function, args=request.args, vars=request.vars)
    return A(name, _href=sort_url)


def table_container(fields, *content):
    table = TABLE(_class="table")
    thead = TR()
    i = -1
    for field in fields:
        i += 1
        th = TH(create_sort_link(field), _class="tcol_%s" % i)

        thead.append(th)
    table.append(THEAD(thead))
    table.append(TBODY(content))

    return table


def record_data(row, fields):
    data = Storage()
    for field in fields:
        # this is the case when the table and field data is specified
        if type(field) == dict:
            t_name = field['table']
            t_fields = field['fields']
            for t_field in t_fields:
                if type(t_field) != str:
                    continue
                print row[t_name][t_field]


def table_element(fields, row, options_function=None):
    el = TR()
    for field in fields:
        td = TD()
        if type(field) == dict:
            for subfield in field['fields']:
                td.append(row[field['ref_field']][subfield])
                td.append(' ')
        else:
            td.append(row[field.name])
        el.append(td)
    return el


def create_content(fields, rows, options_funct, element_generator):
    for row in rows:
        yield element_generator(fields, row, options_funct)


def default_options():
    pass



def TROW(row, fields, options_func):
    pass


def parse_field(field, row, base_table_name):
    header = None
    data = ''
    if type(field) == dict:
        table_name = field['table'] if field.has_key('table') else None
        joined_field_names = ''
        if field.has_key('fields') and type(field['fields']) == list:
            joined_field_names = ' '.join(field['fields'])
            for sub_field in field['fields']:
                if table_name:
                    data += str(row[table_name][sub_field]) + ' '
                else:
                    data += str(row[sub_field]) + ' '
        header = field['label_as'] if field.has_key('label_as') else joined_field_names
    else:
        header = db[base_table_name][field].label
        data = row[field]
    return header, data


def supert(query, select_args={}, fields=[], options_func=default_options):
    """
    about fields, fields is an array of <value> where every <value> is either
    a dict or a string.

    if the <value> is string, then for every row this function will get
    row['<value>'] and use the header db[<default table>][field].label

    if the <value> is a dict, then we can specify the following parameters:
        table:

        fields: []

        label_as:

    """

    rows = db(query).select(**select_args)
    # this is the case when theres no join, or only one table is selected
    table_name = None
    headers = []
    datas = []
    base_table_name = None
    if rows.first():
        base_table_name = rows.colnames[0].split('.')[0]
    headers_added = False
    for row in rows:
        index = 0
        for field in fields:
            header, data = parse_field(field, row, base_table_name)
            if not headers_added:
                headers.append(header)
                datas.append([])
            datas[index].append(data)
            index += 1
        headers_added = True


    table = DIV(_class="supert")
    for index, header in enumerate(headers):
        container = DIV(_class="supert-col")
        container.append(DIV(header, _class="supert-row-data supert-last top"))
        for data in datas[index]:
            container.append(DIV(data, _class="supert-row-data"))
        table.append(container)

    return table
    # content = []
    # for row in rows:
    #     content.append(element(fields, row))
    # return container(fields, *content)
