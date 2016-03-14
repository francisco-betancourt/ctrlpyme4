@auth.requires_membership('Admin')
def index():
    title = T('labels page layouts')
    data = SUPERT(db.labels_page_layout, fields=[
        'name', {
            'fields': ['label_cols', 'label_rows'],
            'label_as': T('Cols x Rows'),
            'custom_format': lambda row, fields: '%s x %s' % (row[fields[0]], row[fields[1]])
        }
    ])

    return locals()

@auth.requires_membership('Admin')
def create():
    return common_create('labels_page_layout')


@auth.requires_membership('Admin')
def update():
    return common_update('labels_page_layout', request.args)


@auth.requires_membership('Admin')
def delete():
    return common_delete('labels_page_layout', request.args)
