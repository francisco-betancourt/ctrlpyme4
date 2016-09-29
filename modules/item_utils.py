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

import urllib
import re
from decimal import Decimal as D
import math
import json
from uuid import uuid4
from gluon.storage import Storage
from gluon import current, SCRIPT, URL, redirect

from common_utils import *


def item_barcode(item):
    return item.sku or item.ean or item.upc


def get_wavg_days_in_shelf(item, id_store=None):
    """ for the specified item returns the total avg_days_in_shelf obtained from all its bag items """

    db = current.db

    avg = db.bag_item.wavg_days_in_shelf.avg()

    q = (db.bag_item.id_bag == db.bag.id) & (db.bag_item.id_item == item)  & (db.bag_item.wavg_days_in_shelf >= 0)
    if id_store:
        q &= db.bag.id_store == id_store

    avg_days_in_shelf = db(q).select(avg).first()[avg]

    if avg_days_in_shelf < 0:
        return None

    return avg_days_in_shelf


def item_url(_name, _id):
    url_name = "%s%s" % (urlify_string(_name), _id)
    return url_name


def item_taxes(item, price):
    """ Returns the amoutn of taxes for the given item and price """
    
    total = 0
    if not item.taxes:
        return 0
    for tax in item.taxes:
        total += (price or 0) * D((tax.percentage or 0) / 100.0)
    return DQ(total)


def item_stock_query(item, id_store=None, include_empty=False, max_date=None):

    db = current.db

    query = (db.stock_item.id_item == item.id)
    if id_store > 0:
        query &= db.stock_item.id_store == id_store
    if not include_empty:
        query &= db.stock_item.stock_qty > 0
    if max_date:
        query &= db.stock_item.created_on < max_date

    return query


def item_stock_iterator(item, id_store=None, include_empty=False, max_date=None):
    """ used to get stock items related to the specified item """

    db = current.db

    query = item_stock_query(item, id_store, include_empty, max_date)

    # services and bundles does not have stocks
    if not item.has_inventory or item.is_bundle:
        return None

    return db(query).iterselect(orderby=db.stock_item.created_on)


def item_stock_qty(item, id_store=None, id_bag=None, max_date=None):
    """ Returns the current stock for the specified item,
        if id_bag is specified, then this function will consider the items in
        the specified bag as not available (removing stock)
    """

    db = current.db
    stocks = None

    # services have unlimited qty
    if not item.has_inventory:
        return 2**64 # hack since theres a problem using float('inf')

    if item.is_bundle:
        bundle_items = db(db.bundle_item.id_bundle == item.id).iterselect()
        if not bundle_items:
            return 0
        min_bundle = float('inf')
        for bundle_item in bundle_items:
            qty = item_stock_qty(bundle_item.id_item, id_store, id_bag, max_date)
            min_bundle = min(min_bundle, qty / bundle_item.quantity)
            if not item.allow_fractions:
                min_bundle = math.floor(min_bundle)
        return D(min_bundle)

    bag_item_count = 0
    if id_bag:
        # check bundle items containing the specified item
        count_sum = (db.bundle_item.quantity * db.bag_item.quantity).sum()
        bundle_items_count = db(
            (db.bundle_item.id_bundle == db.bag_item.id_item)
           & (db.bag_item.id_item == db.item.id)
           & (db.bundle_item.id_item == item.id)
           & (db.item.is_bundle == True)
           & (db.bag_item.id_bag == id_bag)
        ).select(count_sum).first()[count_sum] or 0

        # this is the specified item
        count_sum = db.bag_item.quantity.sum()
        item_count = db(
            (db.bag_item.id_item == item.id)
          & (db.bag_item.id_bag == id_bag)
          & (db.bag_item.quantity > 0)
        ).select(count_sum).first()[count_sum] or 0

        bag_item_count = bundle_items_count + item_count

    stock_sum = db.stock_item.stock_qty.sum()
    query = item_stock_query(item, id_store, None, max_date)
    stocks_qty = db(query).select(stock_sum).first()[stock_sum] or 0

    return stocks_qty - bag_item_count


def item_discounts(item):
    """ returns the maximum applicable discounts for the specified item """
    db = current.db
    request = current.request

    # get the current offer groups
    offer_groups = db((db.offer_group.starts_on < request.now) & (db.offer_group.ends_on > request.now)).select()
    if not offer_groups:
        return []

    final_query = db.discount.id < 0
    base_query = (db.discount.is_coupon == False) & (db.discount.code == '')
    for offer_group in offer_groups:
        # for every group query all applicable discounts
        query = db.discount.id_item == item.id
        if item.id_brand:
            query |= db.discount.id_brand == item.id_brand.id
        for category in item.categories:
            query |= db.discount.id_category == category.id
        query &= db.discount.id_offer_group == offer_group.id
        final_query |= query
    final_query &= base_query

    # combinable discounts
    c_discounts = db(final_query & (db.discount.is_combinable == True)).select()
    # non combinable discounts
    nc_discounts = db(final_query & (db.discount.is_combinable == False)).select()

    # calculate the sum of combinable discounts
    c_discounts_p = 0
    for c_discount in c_discounts:
        c_discounts_p += c_discount.percentage
    # get the maximum no combinable discount
    if nc_discounts:
        max_nc_discount = nc_discounts.first()
        for nc_discount in nc_discounts:
            if max_nc_discount.percentage < nc_discount.percentage:
                max_nc_discount = nc_discount
    else:
        return c_discounts
    # return the max discount
    if max_nc_discount.percentage > c_discounts_p:
        return [max_nc_discount]
    else:
        return c_discounts


def discount_data(discounts, price):
    if not price:
        return D(0), D(0)
    new_price = price
    for discount in discounts:
        new_price -= new_price * D(discount.percentage / 100.0)
    return new_price, (D(1.0) - (new_price / price)) * D(100)

def apply_discount(discounts, price):
    return discount_data(discounts, price)[0]

def get_discount_percentage(bag_item):
    return (D(1) - bag_item.sale_price / (bag_item.sale_price + bag_item.discount)) * D(100)


def fix_item_price(item, price):
    """ modifies the item data based on discounts and taxes """

    price = D(0) if not price else price
    new_price = price
    discounts = item_discounts(item)
    for discount in discounts:
        new_price -= new_price * DQ(discount.percentage / 100.0)
    new_price += item_taxes(item, new_price)

    item.new_price = (price or 0) + item_taxes(item, price)
    discount_percentage = 0
    try:
        # unable to calculate discount percentage with new price 0
        discount_percentage = int((1 - (new_price / item.new_price)) * 100)
    except:
        pass
    item.new_price = str(DQ(item.new_price, True))
    item.discounted_price = str(DQ(new_price, True))
    item.discount_percentage = discount_percentage



def fix_item_quantity(item, quantity):
    """ given an item and a quantity, returns a fixed quantity based on the item allow_fraction parameter """

    quantity = max(0, quantity)  # does not allow negative quantities
    if item.allow_fractions:
        return DQ(quantity, True)
    else:
        return remove_fractions(quantity)


def active_item(item_id):
    db = current.db
    return db((db.item.id == item_id) & (db.item.is_active == True)).select().first()


def undo_stock_removal(bag=None, inventory=None, remove=True):
    """ Reintegrates the removed stocks given a bag or inventory """

    db = current.db

    stock_removals = None
    delete_query = None
    if bag:
        stock_removals = db(
            (db.stock_item_removal.id_bag_item == db.bag_item.id)
            & (db.bag_item.id_bag == db.bag.id)
            & (db.bag.id == bag.id)
        ).select(db.stock_item_removal.ALL)
        delete_query = db.bag.id == bag.id
    elif inventory:
        stock_removals = db(
            (db.stock_item_removal.id_inventory_item == db.inventory_item.id)
            & (db.inventory_item.id_inventory == db.inventory.id)
            & (db.inventory.id == inventory.id)
        ).select(db.stock_item_removal.ALL)
        delete_query = db.stock_item.id_inventory == inventory.id
        if remove:
            delete_query = db.inventory.id == inventory.id
    else:
        return
    for stock_removal in stock_removals:
        stock_item = db.stock_item(stock_removal.id_stock_item.id)
        stock_item.stock_qty += stock_removal.qty
        stock_item.update_record()
    db(delete_query).delete()


def _remove_stocks(item, remove_qty, sale_date, bag_item=None,
                   inventory_item=None):
    """ remove the specified item quantity from available stocks
        if a bag_item is specified this function will create stock_item_removal
        records associated with the specified bag.
    """
    session = current.session
    db = current.db

    if not item.has_inventory or not remove_qty:
        return 0, 0

    stock_items = item_stock_iterator(item, session.store)
    stock_qty = item_stock_qty(item, session.store)
    if not stock_qty:
        return 0, 0

    remaining_remove_qty = remove_qty
    total_buy_price = 0
    wavg_days_in_shelf = 0
    for stock_item in stock_items:
        # the amount of items that will be removed from the current stock
        to_be_removed_qty = min(stock_item.stock_qty, remaining_remove_qty)
        stock_item.stock_qty -= to_be_removed_qty
        stock_item.update_record()
        remaining_remove_qty -= to_be_removed_qty

        total_buy_price += to_be_removed_qty * (stock_item.price or 0)
        days_since_purchase = (sale_date - stock_item.created_on).days
        wavg_days_in_shelf += days_since_purchase

        # this could replace wavg_days_in shelf or we could recalculate it
        if bag_item:
            db.stock_item_removal.insert(
                id_stock_item=stock_item.id,
                qty=to_be_removed_qty,
                id_bag_item=bag_item.id,
                id_item=item.id,
                id_store=stock_item.id_store.id
            )
        elif inventory_item:
            db.stock_item_removal.insert(
                id_stock_item=stock_item.id,
                qty=to_be_removed_qty,
                id_inventory_item=inventory_item.id,
                id_item=item.id,
                id_store=stock_item.id_store.id
            )

    wavg_days_in_shelf /= remove_qty

    return total_buy_price, wavg_days_in_shelf


def remove_stocks(bag_items):
    """ Remove stocks for all the bag items specified """
    db = current.db

    id_bag = None
    for bag_item in bag_items:
        if not id_bag:
            id_bag = bag_item.id_bag.id

        #TODO:50 implement stock removal for bag items with serial number
        if bag_item.id_item.has_serial_number:
            pass
        else:
            bag_item_total_buy_price = 0
            # when we have a bundle, we have to remove stocks for every item in the bundle. Since bundles cannot be purchased, we have to consider its average days in shelf, as the average of its bundle items weighted average days in shelf
            if bag_item.id_item.is_bundle:
                total_wavg_days_in_shelf = 0
                bundle_items_qty = 0
                bundle_items = db(
                    db.bundle_item.id_bundle == bag_item.id_item.id
                ).select()
                for bundle_item in bundle_items:
                    bundle_items_qty += 1
                    total_buy_price, wavg_days_in_shelf = _remove_stocks(
                        bundle_item.id_item,
                        bundle_item.quantity * bag_item.quantity,
                        bag_item.created_on,
                        bag_item
                    )
                    total_wavg_days_in_shelf += wavg_days_in_shelf
                    bag_item_total_buy_price += total_buy_price
                total_wavg_days_in_shelf /= bundle_items_qty

                bag_item.total_buy_price = bag_item_total_buy_price
                bag_item.wavg_days_in_shelf = total_wavg_days_in_shelf
            else:
                total_buy_price, wavg_days_in_shelf = _remove_stocks(
                    bag_item.id_item,
                    bag_item.quantity,
                    bag_item.created_on,
                    bag_item
                )
                bag_item.total_buy_price = total_buy_price
                bag_item.wavg_days_in_shelf = wavg_days_in_shelf

            bag_item.update_record()

    db(db.bag.id == id_bag).update(is_delivered=True)


def reintegrate_stock(item, returned_qty, avg_buy_price, target_field, target_id):
    db = current.db
    session = current.session

    stock_item = db(
        (db.stock_item[target_field] == target_id) & (db.stock_item.id_item == item.id)
    ).select().first()
    if stock_item:
        stock_item.purchase_qty += returned_qty
        stock_item.stock_qty += returned_qty
        stock_qty.update_record()
    else:
        target_data = {target_field: target_id}
        db.stock_item.insert(
            id_item=item.id,
            purchase_qty=returned_qty,
            price=avg_buy_price,
            stock_qty=returned_qty,
            id_store=session.store,
            taxes=0, **target_data
        )


def reintegrate_bag_item(bag_item, quantity, new_stock=False,
    target=None, target_id=None
):
    """ Return removed item to their exact stock item, except when the target is credit_note, in that case this will create a new stock """

    db = current.db
    request = current.request
    session = current.session


    def items_iterator(bag_item):
        # Iterate over all the items referenced by the bag_item, if the bag_item contains a bundle then this iterator will return all the bundle items, in other case it will return just the item

        if bag_item.id_item.is_bundle:

            bundle_items = db(
                db.bundle_item.id_bundle == bag_item.id_item.id
            ).iterselect()

            for bundle_item in bundle_items:
                yield bundle_item.id_item, bundle_item.quantity * quantity
        else:
            yield bag_item.id_item, quantity


    for item, qty in items_iterator(bag_item):

        item_removals = db(
            (db.stock_item_removal.id_bag_item == bag_item.id) &
            (db.stock_item_removal.id_item == item.id)
        ).iterselect()

        # the remaining items to be reintegrated
        remaining = quantity

        # instead of reintegrating to the exact stock, create a new one.
        if new_stock:
            # get avg removals data
            price = 0
            taxes = 0
            count = 0
            for item_removal in item_removals:
                price += item_removal.id_stock_item.price or 0
                taxes += item_removal.id_stock_item.taxes or 0
                count += 1
            price /= count
            taxes /= count

            if not target or not target_id:
                raise ValueError("target or target id not specified")
            params = dict(
                purchase_qty=remaining, stock_qty=remaining,
                id_store=session.store, id_item=item.id,
                price=price, taxes=taxes
            )
            params[target] = target_id
            params['created_on'] = request.now
            params['modified_on'] = request.now
            new_id = db.stock_item.insert( **params )
        else:
            for item_removal in item_removals:

                if not remaining > 0:
                    break

                # the stock from which the items were removed
                stock_item = db(
                    db.stock_item.id == item_removal.id_stock_item.id
                ).select().first()

                # this operation is safe if stock item removals are correct
                reintegrated_qty = min(
                    min(qty, stock_item.purchase_qty), item_removal.qty
                )
                stock_item.stock_qty += reintegrated_qty

                stock_item.update_record()

            remaining -= reintegrated_qty

            item_removal.qty -= reintegrated_qty

            if not item_removal.qty > 0:
                # delete stock removal
                item_removal.delete_record()
            else:
                item_removal.update_record()



def create_traits_ref_list(traits_str):
    """ given a string of encoded traits, create a list of ids for every trait, creating them if they do not exist.

        trait string format is a comma separated list of:
        category_name:trait_option
    """

    db = current.db

    traits = []
    # only accept the first 10 traits
    for pair in traits_str.split(',')[:10]:
        category_name, option = pair.split(':')[:2]
        trait_cat_id = db(
            db.trait_category.name == category_name
        ).select().first()
        if not trait_cat_id:
            trait_cat_id = db.trait_category.insert(name=category_name)
        else:
            trait_cat_id = trait_cat_id.id
        trait_id = db(
            (db.trait.id_trait_category == trait_cat_id)
            & (db.trait.trait_option == option)
        ).select().first()
        if not trait_id:
            trait_id = db.trait.insert(
                trait_option=option,
                id_trait_category=trait_cat_id
            )
        else:
            trait_id = trait_id.id
        traits.append(trait_id)

    return traits or []



def search_item_query(str_term, category):
    """
        Generates a query to search items with the specified term and category
    """

    db = current.db

    term = str_term.split(' ')

    query = (db.item.name.contains(term, all=True))
    query |= db.item.sku.like(term[0] + '%')
    query |= db.item.ean.like(term[0] + '%')
    query |= db.item.upc.like(term[0] + '%')

    categories_data_script = SCRIPT()
    if not category:
        matched_categories = db(
            db.category.name.contains(term)
        ).iterselect()
        matched_categories_ids = []
        for matched_category in matched_categories:
            matched_categories_ids.append(str(matched_category.id))
        # search by category
        if matched_categories_ids:
            query |= db.item.categories.contains(
                matched_categories_ids, all=False
            )

    # search by Brands
    matched_brands = db(db.brand.name.contains(term)).iterselect()
    for matched_brand in matched_brands:
        query |= db.item.id_brand == matched_brand.id

    # search by trait
    matched_traits = (str(i.id) for i in db(db.trait.trait_option.contains(term)).iterselect(db.trait.id))
    if matched_traits:
        query |= db.item.traits.contains(matched_traits, all=False)

    query &= db.item.is_active == True

    if not term:
        query = db.item.is_active == True

    return query


def concat_traits(item):
    c_name = ""

    if item.traits:
        for trait in item.traits:
            c_name += ' ' + trait.trait_option

    return c_name


def composed_name_data(item):
    """ Returns extra data that can be added to the item name """

    c_name = ""

    c_name = concat_traits(item)
    if not c_name and item.description:
        c_name += item.description[:10]
        if len(item.description) > 10:
            c_name += '...'

    return c_name


def composed_name(item):
    """ Returns the item name with some extra data, like its traits or short description if any """

    return item.name + composed_name_data(item)


def data_for_card(item):
    """ Returns item information to fill a card """

    session = current.session
    T = current.T
    db = current.db
    auth = current.auth

    memberships = dict([(v, True) for v in auth.user_groups.values()])


    if not item:
        return None

    available = "Not available"
    stock_qty = item_stock_qty(item, session.store)
    if stock_qty > 0:
        available = "Available"
    item.availability = Storage( available=stock_qty > 0, text=str(T(available)) )

    image = db(
        (db.item_image.id_item == db.item.id)
      & (db.item.id == item.id)
      & (db.item.is_active == True)
    ).select(db.item_image.sm).first()
    item.image_path = URL('static', 'uploads/' + image.sm) if image else URL('static', 'images/no_image.svg')


    item_price = (item.base_price or 0) + item_taxes(item, item.base_price)
    fix_item_price(item, item.base_price)
    item.price = item.discounted_price

    item.barcode = None

    # extra options for employees
    item.options = []
    if memberships.get('Employee'):
        item.barcode = item_barcode(item)

        if memberships.get('Items info') or memberships.get('Items management') or memberships.get('Items prices'):
            item.options.append((
                T('Update'), URL('item', 'update', args=item.id)
            ))
            item.options.append((
                T('Print labels'), URL('item', 'labels', args=item.id)
            ))
            item.options.append((
                T('Add images'), URL('item_image', 'create', args=item.id)
            ))
        if memberships.get('Analytics'):
            item.options.append((
                T('Analysis'), URL('analytics', 'item_analysis', args=item.id)
            ))

    item = Storage(
        id=item.id,
        name=item.name,
        name_extra=composed_name_data(item),
        availability=item.availability,
        image_path=item.image_path,
        brand=Storage(
            id=item.id_brand.id,
            name=item.id_brand.name
        ),
        base_price=float(item.base_price),
        discount=float(item.discount_percentage),
        price=float(item.price)
    )
    return item
