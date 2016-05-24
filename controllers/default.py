# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

from datetime import date, datetime
import random


def index():
    # best sellers this month
    start_date = date(request.now.year, request.now.month, 1)
    end_date = date(request.now.year, request.now.month + 1, 1)

    values = db(
        (db.bag_item.id_item == db.item.id)
        & (db.bag_item.created_on >= start_date)
        & (db.bag_item.created_on <= end_date)
    ).select(db.item.ALL, db.bag_item.quantity.sum(), groupby=db.item.id, limitby=(0, 10), orderby=~db.bag_item.quantity.sum(), cache=(cache.ram, 3600), cacheable=True)
    popular_items = [v.item for v in values]
    random.shuffle(popular_items)

    new_items = db(db.item.is_active == True).select(orderby=~db.item.created_on, limitby=(0, 10), cache=(cache.ram, 3600), cacheable=True)

    services = db((db.item.is_active == True) & (db.item.has_inventory == False)).select(orderby='<random>', limitby=(0, 10), cache=(cache.ram, 3600), cacheable=True)

    rand_categories = db((db.category.is_active == True)).select(orderby='<random>', limitby=(0, 10), cache=(cache.ram, 3600), cacheable=True)

    highlights = db((db.highlight.id_store == session.store)
                  | (db.highlight.id_store == None)
                  ).select(cache=(cache.ram, 3600), cacheable=True)

    offers = db((db.offer_group.starts_on < request.now)
              & (db.offer_group.ends_on > request.now)
              ).select(cache=(cache.ram, 3600), cacheable=True)

    stores = db(db.store.is_active == True).select(cache=(cache.ram, 3600), cacheable=True)

    page_title = T('Start page')
    categories_string = ', '.join([cat.name for cat in rand_categories])
    page_description = T('Shop online') + ' ' + T('categories') + ': ' + categories_string
    PRELOAD(enable_calendar=False, enable_supert=False, enable_treeview=False,
            enable_css_ticket=False)
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
