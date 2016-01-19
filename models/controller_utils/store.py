print "Store model"

def create_store():
    id_address = request.vars.id_address
    form = SQLFORM(db.store)
    form.id_address = id_address
    if form.process().accepted:
        # insert store group
        db.auth_group.insert(role='Store %s' % form.vars.id)
        response.flash = T('form accepted')
        redirect(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)
