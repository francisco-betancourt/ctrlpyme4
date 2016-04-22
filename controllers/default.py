# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

from datetime import date
from item_utils import get_popular_items

def index():
    # best sellers this month
    start_date = date(request.now.year, request.now.month, 1)
    end_date = date(request.now.year, request.now.month + 1, 1)
    pop_items = get_popular_items(start_date, end_date)
    popular_items = [d[0] for d in pop_items[:10]]

    new_items = db(db.item.is_active == True).select(orderby=~db.item.created_on, limitby=(0, 10))

    highlights = db((db.highlight.id_store == session.store)
                  | (db.highlight.id_store == None)
                  ).select()

    offers = db((db.offer_group.starts_on < request.now)
              & (db.offer_group.ends_on > request.now)
              ).select()

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
