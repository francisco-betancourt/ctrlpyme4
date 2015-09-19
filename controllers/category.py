# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

import urllib
import re


rmap = {  'á': 'a', 'Á': 'a' , 'é': 'e', 'É': 'e' , 'í': 'i', 'Í': 'i'
        , 'ó': 'o', 'Ó': 'o' , 'ú': 'u', 'Ú': 'u'
       }
def replace_match(match):
    key = match.group(0)
    print key
    if rmap.has_key(key):
        return rmap[key]
    return ""
regex = re.compile('(á|é|í|ó|ú|Á|É|Í|Ó|Ú)')

def urlify_string(string):
    s = regex.sub(replace_match, string)
    s = urllib.quote(s)
    return s



def create():
    redirect_url = URL('index')
    parent = db.category(request.vars.parent)

    form = SQLFORM(db.category)

    if parent:
        redirect_url = URL('get', args=parent.id)
        form = SQLFORM(db.category, fields=['name', 'description', 'url_name', 'icon', 'trait_category1', 'trait_category2', 'trait_category3'])
        form.vars.parent = parent.id

    if form.process().accepted:
        url_name = "%s%s" % (urlify_string(form.vars.name), form.vars.id)
        db.category(form.vars.id).update_record(url_name=url_name)
        response.flash = T("category created")
        redirect(redirect_url)
    elif form.errors:
        response.flash = T('form has errors')

    return dict(form=form)


def get():
    category = db.category(request.args(0))
    if not category:
        redirect(URL('index'))
    rows = db(db.category.parent == category.id).select()
    return locals()


def update():
    category = db.category(request.args(0))
    if not category:
        raise HTTP(400)
    redirect_url = URL('index')
    parent = category.parent

    form = SQLFORM(db.category, category)

    if parent:
        redirect_url = URL('get', args=parent.id)
        form = SQLFORM(db.category, category, fields=['name', 'description', 'url_name', 'icon', 'trait_category1', 'trait_category2', 'trait_category3'])

    if form.process().accepted:
        url_name = "%s%s" % (urlify_string(form.vars.name), form.vars.id)
        db.category(form.vars.id).update_record(url_name=url_name)
        response.flash = T("category created")
        redirect(redirect_url)
    elif form.errors:
        response.flash = T('form has errors')

    return dict(form=form, category=category)


def delete():
    return common_delete('category', request.args)


def index():
    rows = db(db.category.parent == None).select()
    return locals()
