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


# This module is used to update specific data when there are changes in the
# database that need to be retroactive
#


from gluon import current

def update_stock_item_removals():
    """ Update stock item removals when they have missing auth.signature data and no store 
    """
    db = current.db

    for sir in db(db.stock_item_removal.id > 0).iterselect():
        sir.id_store = sir.id_stock_item.id_store.id
        if sir.id_bag_item:
            sir.created_on = sir.id_bag_item.id_bag.created_on 
            sir.modified_on = sir.id_bag_item.id_bag.modified_on 
            sir.created_by = sir.id_bag_item.id_bag.created_by
            sir.modified_by = sir.id_bag_item.id_bag.modified_by
        elif sir.id_inventory_item:
            sir.created_on = sir.id_inventory_item.id_inventory.created_on 
            sir.modified_on = sir.id_inventory_item.id_inventory.modified_on 
            sir.created_by = sir.id_inventory_item.id_inventory.created_by
            sir.modified_by = sir.id_inventory_item.id_inventory.modified_by
        sir.update_record()