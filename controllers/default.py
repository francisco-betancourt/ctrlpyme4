# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    # response.flash = T("Hello World")

    new_items = db(db.item.is_active == True).select(orderby=~db.item.created_on, limitby=(0, 5), groupby=db.item.name)

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



# #TODO:100 remove from here
def create_groups():
    groups = {
          "Admin": ""
        , "Inventories": ""
        , "Purchases": ""
        , "Items": ""
        , "Merchandise delivery": ""
        , "Changes and returns": ""
        , "Invoices": ""
        , "Drop item": ""
        , "Promotions": ""
        , "Payment options": ""
        , "Clients": ""
        , "Suppliers": ""
        , "Categories": ""
        , "Measure units": ""
        , "Brands": ""
        , "Taxes": ""
        , "Accounts Payable": ""
        , "Accounts Receivable": ""
        , "Analytics": ""
        , "Pages": "" # Could be Layout
        , "Menus": "" #
        , "Sales": ""
        , "Cashiers": ""
        , "Prices": ""
        , "Bundles": ""
    }

    new_groups = {
          "Admin": "All included"
        , "Manager": "Accounts (Payable | Receivable), Analytics, Suppliers, Taxes"
        , "Inventories": "Create and apply inventories"
        , "Purchases": "Make Purchases"
        , "Items info": "Modify basic item information"
        , "Items management": "Modify brands, categories, hide and show items and create promotions, item drops (lost or damaged items), create items"
        , "Items prices": "Allows item price modification"

        , "Sales bags": "Bag creation and modification"
        , "Sales checkout": "Users in this group will be able to create a sale, register money income"
        , "Sales delivery": "Allows the modification of stocks and serial number capture for sold items"
        , "Sales invoices": "Invoice creation and cancellation, folios management"
        , "Sales returns": "Items returns"

        , "Clients": "Create clients"
        , "Cashiers": "Sale creation"
        , "Page layout": "Menus, pages, colors, logo and visual configuration"
        , "VIP seller": "Allows price2 and price3 selection"
        , "Employee": "An Employee"
        , "Analytics": "Users in this group have acces to the analytic tools"
    }


    for key in new_groups.iterkeys():
        if db(db.auth_group.role == key).select().first():
            continue
        auth.add_group(key, new_groups[key])
