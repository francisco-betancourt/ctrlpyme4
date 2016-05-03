# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

from datetime import date, datetime


def get_popular_items(start_date, end_date, amount=10, id_store=None):
    """ Naive method to get the most bagged items """

    # first of all, check the cached data
    cached = db(db.cached_data.name == CACHED_POPULAR_ITEMS).select().first()
    if cached:
        cache_lifetime = request.now - cached.modified_on
        # recalculate after 2 hours
        if cache_lifetime < timedelta(minutes=120):
            try:
                ids = map(int, cached.val.split(','))
            except:
                return []
            return db(db.item.id.belongs(ids)).select(orderby='<random>')
    else:
        cached_id = db.cached_data.insert(name=CACHED_POPULAR_ITEMS)
        cached = db.cached_data(cached_id)

    q_sum = db.bag_item.quantity.sum()
    data = []
    for item in db(db.item.is_active == True).select():
        query = db.bag_item.id_bag == db.bag.id
        query &= db.bag_item.id_item == item.id
        if start_date:
            query &= db.bag_item.created_on >= start_date
        if end_date:
            query &= db.bag_item.created_on <= end_date
        if id_store:
            query &= db.bag.id_store == id_store
        counter = db(query).select(q_sum).first()[q_sum] or 0
        data.append((item, counter))
    data.sort(key=lambda tup: tup[1], reverse=True)
    data = data[:amount]
    data = [d[0] for d in data] # remove counter
    # update chache
    cached.val = ','.join(map(lambda x: str(x.id), data))
    cached.modified_on = request.now
    cached.update_record()
    return data


def index():
    # best sellers this month
    start_date = date(request.now.year, request.now.month, 1)
    end_date = date(request.now.year, request.now.month + 1, 1)
    popular_items = get_popular_items(start_date, end_date)

    new_items = db(db.item.is_active == True).select(orderby=~db.item.created_on, limitby=(0, 10))

    highlights = db((db.highlight.id_store == session.store)
                  | (db.highlight.id_store == None)
                  ).select()

    offers = db((db.offer_group.starts_on < request.now)
              & (db.offer_group.ends_on > request.now)
              ).select()

    stores = db(db.store.is_active == True).select()

    return locals()


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
