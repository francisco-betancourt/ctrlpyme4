

def offer_group_table():
    title = T('Offer groups')
    data = SUPERT((db.offer_group), fields=[
        'name', 'id_store', 'starts_on', 'ends_on'
    ])

    return locals()


def paper_size_table():
    title = T('Paper sizes')
    data = SUPERT(db.paper_size, fields=[
        'name', 'width', 'height'
    ], options_enabled=False)

    return locals()


@auth.requires_membership('Admin')
def labels_page_layout_table():
    title = T('Labels page layouts')
    data = SUPERT(db.labels_page_layout, fields=[
        'name', {
            'fields': ['label_cols', 'label_rows'],
            'label_as': T('Cols x Rows'),
            'custom_format': lambda row, fields: '%s x %s' % (row[fields[0]], row[fields[1]])
        }
    ])

    return locals()


@auth.requires_membership('Admin')
def store_table():
    def store_options(row):
        update_btn, hide_btn = supert_default_options(row)
        return update_btn, hide_btn, OPTION_BTN('vpn_key', URL('seals', args=row.id))
    title = T('Stores')
    data = SUPERT(db.store, fields=[
        'name'
    ], options_func=store_options)

    return locals()


generators = dict(
      offer_group=offer_group_table
    , paper_size=paper_size_table
    , labels_page_layout=labels_page_layout_table
    , store=store_table
)


def get_table():
    request.controller = request.args(0)
    return generators[request.args(0)]()
