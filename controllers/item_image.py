# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

from PIL import Image


def create():
    """ args: [id_item] """

    item = db.item(request.args(0))
    if not item:
        raise HTTP(404)

    images = db(db.item_image.id_item == item.id).select()

    form = SQLFORM(db.item_image)
    form.id_item = item.id

    if form.process().accepted:
        db(db.item_image.id == form.vars.id).update(id_item=item.id)

    return locals()
