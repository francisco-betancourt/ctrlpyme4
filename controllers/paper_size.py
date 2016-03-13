@auth.requires_membership('Admin')
def index():
    redirect(URL('common', 'get_table', args='paper_size'))

    return locals()


@auth.requires_membership('Admin')
def create():
    form = SQLFORM(db.paper_size)

    if form.process().accepted:
        session.info = T("Paper size created")
        redirect(URL('index'))

    return locals()
