# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

from PIL import Image
import os


sizes = [(48, 48), (250, 250), (500, 500), (1000, 1000)]
sizes_names = ['thumb', 'sm', 'md', 'lg']


def create():
    """ args: [id_item] """

    item = db.item(request.args(0))
    if not item:
        raise HTTP(404)

    images = db(db.item_image.id_item == item.id).select()

    form = SQLFORM(db.item_image)
    form.id_item = item.id

    if form.process().accepted:
        item_image = db.item_image(form.vars.id)
        item_image.id_item = item.id
        img_path = os.path.join(request.folder, 'uploads', item_image.image)
        img = Image.open(img_path)
        outfile = os.path.splitext(img_path)[0]
        img_width, img_height = img.size

        i = 0
        for size in sizes:
            try:
                img = Image.open(img_path)
                new_file_name = outfile
                new_file_name += '.thumbnail' if sizes_names[i] == 'thumb' else '_%s.jpg' % sizes_names[i]
                img.thumbnail(size, Image.ANTIALIAS)
                img.save(new_file_name, 'JPEG')
                img_file = open(new_file_name)
                item_image[sizes_names[i]] = img_file
                i += 1
            except IOError:
                import traceback as tb
                tb.print_exc()
        item_image.update_record()

    return locals()
