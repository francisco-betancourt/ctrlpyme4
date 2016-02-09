@auth.requires_membership('Admin')
def index():
    data = super_table('paper_size', ['name', 'width', 'height'], db.paper_size, options_enabled=False)

    return locals()


@auth.requires_membership('Admin')
def create():
    form = SQLFORM(db.paper_size)

    if form.process().accepted:
        session.info = T("Paper size created")
        redirect(URL('index'))

    return locals()
