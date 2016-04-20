# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bet@net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Author Daniel J. Ramirez <djrmuv@gmail.com>

from PIL import Image
import os


sizes = [(48, 48), (250, 250), (500, 500), (1000, 1000)]
sizes_names = ['thumb', 'sm', 'md', 'lg']


@auth.requires_membership('Items info')
def create():
    """ args: [id_item] """

    item = db.item(request.args(0))
    if not item:
        raise HTTP(404)

    session._next = URL('create', args=request.args)

    images = db(db.item_image.id_item == item.id).select()

    form = SQLFORM(db.item_image,
        buttons=[
            TAG.button(T('Add'), _type='submit', _class="btn btn-primary"),
            A(T('Finish'), _class='btn btn-default', _href=URL('item', 'get_item', args=item.id))
        ], formstyle='bootstrap'
    )
    form.id_item = item.id

    if form.process().accepted:
        item_image = db.item_image(form.vars.id)
        item_image.id_item = item.id
        img_path = os.path.join(request.folder, 'static/uploads/', item_image.image)
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
        i = 0
        for size in sizes:
            new_file_name = outfile
            new_file_name += '.thumbnail' if sizes_names[i] == 'thumb' else '_%s.jpg' % sizes_names[i]
            os.remove(new_file_name)
            i += 1
        redirect(URL(request.function, args=request.args))

    return locals()


@auth.requires_membership('Items info')
def delete():
    """
        args: [item_image_id]
    """

    db(db.item_image.id == request.args(0)).delete()

    redirection()
