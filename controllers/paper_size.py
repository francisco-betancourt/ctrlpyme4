@auth.requires_membership('Admin')
def index():
    title = T('paper sizes')
    data = SUPERT(db.paper_size, fields=[
        'name', 'width', 'height'
    ], options_enabled=False)

    return locals()


@auth.requires_membership('Admin')
def create():
    form = SQLFORM(db.paper_size)

    if form.process().accepted:
        session.info = T("Paper size created")
        redirect(URL('index'))

    return locals()
