# create extra Options
if auth.is_logged_in():
    if not session.store:
        stores = db(db.store.is_active == True).select()
        if len(stores) == 1:
            session.store = stores.first().id
    else:
        if not auth.has_membership('Store %s' % session.store) and not auth.has_membership('Admin'):
            redirect(URL('user', 'store_selection'))

    # redirect to store selection, when the user is a employee
    if not session.store and (request.controller != 'user' or request.function != 'store_selection') and auth.has_membership('Employee'):
        redirect(URL('user', 'store_selection'))

    # create a bag in case the user does not have one
    not_bag = ((not session.current_bag) or db.bag(session.current_bag).completed) == 'True'
    if not_bag:
        if auth.has_membership('Clients'):
            bag = db(
                (db.bag.created_by == auth.user.id)
                & (db.bag.completed == False)
            ).select().first()
            if not bag:
                new_bag_id = db.bag.insert(created_by=auth.user.id, completed=False)
                session.current_bag = new_bag_id
            else:
                session.current_bag = bag.id
        elif auth.has_membership('Employee') or auth.has_membership('Admin'):
            bag = db(
                (db.bag.created_by == auth.user.id)
                & (db.bag.id_store == session.store)
                & (db.bag.completed == False)
            ).select().first()
            if not bag:
                new_bag_id = db.bag.insert(created_by=auth.user.id, completed=False, id_store=session.store)
                session.current_bag = new_bag_id
            else:
                session.current_bag = bag.id
