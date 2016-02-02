
def update_main():
    """ Updates the main configuration """

    settings = db(db.settings.id_store == None).select().first()
    form = SQLFORM(db.settings, settings, showid=False)

    return locals()
