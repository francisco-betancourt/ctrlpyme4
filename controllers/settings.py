
def update_main():
    """ Updates the main configuration """

    settings = db(db.settings.id_store == None).select().first()
    if not settings:
        raise HTTP(404)

    form = SQLFORM(db.settings, settings, showid=False, submit_button=T('Save'))
    if form.process().accepted:
        response.flash = T('form accepted')
        redirect(URL('update_main'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)

    return locals()
