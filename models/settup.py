# create extra Options

if auth.is_logged_in():
    # redirect to store selection, when the user is a employee
    if not session.store and (request.controller != 'user' or request.function != 'store_selection') and auth.has_membership('Employee'):
        redirect(URL('user', 'store_selection'))

    # create a bag in case the user does not have one
    bag = db(
        (db.bag.created_by == auth.user.id)
        & (db.bag.completed == False)
    ).select().first()
    if not bag:
        new_bag_id = db.bag.insert(created_by=auth.user.id, completed=False)
        session.current_bag = new_bag_id
