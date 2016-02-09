@auth.requires_membership('Admin')
def index():
    data = super_table('labels_page_layout', ['name'], db.paper_size)

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
