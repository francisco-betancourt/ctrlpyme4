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


from gluon import current


class IS_BARCODE_AVAILABLE(object):
    T = current.T

    """ checks if the object barcode has been already used """

    def __init__(self, db, barcode='', error_message=T('Barcode already used')):
        self.db = db;
        self.barcode = barcode
        self.error_message = error_message
        self.record_id = None
    def set_self_id(self, id):
        self.record_id = id
    def __call__(self, value):
        if not value:
            return (value, None)

        barcodes = None
        # update case
        if self.record_id:
            barcodes = self.db((self.db.item.id != self.record_id)
                               & ((self.db.item.sku == self.barcode)
                                | (self.db.item.ean == self.barcode)
                                | (self.db.item.upc == self.barcode))
                             ).select().first()
        # creation case
        else:
            barcodes = self.db((self.db.item.sku == self.barcode)
                             | (self.db.item.ean == self.barcode)
                             | (self.db.item.upc == self.barcode)
                             ).select().first()
        if not barcodes:
            return (value, None)
        else:
            return (value, self.error_message)
    def formatter(self, value):
        return value


# class HAS_BARCODE(object):
#     def __init__(self, sku, ean, upc, error_message=T('Barcode already used')):
#         self.barcode1 = sku
#         self.barcode2 = ean
#         self.barcode3 = upc
#         self.error_message = error_message
#     def __call__(self, value, value2, value3):
#         if not (value or value2 or value3):
#             return ()
#         if not value:
#             return (value, None)
#         barcodes = self.db((self.db.item.sku == self.barcode)
#                     | (self.db.item.ean == self.barcode)
#                     | (self.db.item.upc == self.barcode)
#                      ).select()
#         if not barcodes:
#             return (value, None)
#         else:
#             return (value, self.error_message)
#     def formatter(self, value):
#         return value
