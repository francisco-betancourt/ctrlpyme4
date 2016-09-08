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
import constants


def set_access_card(user, card_index, company_workflow):
    db = current.db
    auth = current.auth

    card_data = constants.WORKFLOW_DATA[company_workflow].card(card_index)
    # remove all memberships
    memberships_query = (db.auth_membership.user_id == user.id)
    for store_group in db(db.auth_group.role.like('Store %')).select():
        memberships_query &= (db.auth_membership.group_id != store_group.id)
    employee_group = db(db.auth_group.role == 'Employee').select().first()
    if employee_group:
        memberships_query &= (db.auth_membership.group_id != employee_group.id)
    db(memberships_query).delete()

    # add access card memberships
    for role in card_data.groups():
        group = db(db.auth_group.role == role).select().first()
        if group:
            auth.add_membership(group_id=group.id, user_id=user.id)
    user.access_card_index = card_index
    user.update_record()


def update_employees_access_cards():
    """ Used to update employee memberships after workflow membership
        changes, this function is meant to be used by DEVELOPERS migrating
        memberships.
    """

    db = current.db

    query = (
        (db.auth_membership.user_id == db.auth_user.id) &
        (db.auth_membership.group_id == db.auth_group.id) &
        (db.auth_group.role == 'Employee')
    )
    for employee in db(query).iterselect(db.auth_user.ALL):
        try:
            set_access_card(employee, employee.access_card_index, constants.FLOW_BASIC)
        except:
            import traceback as tb
            tb.print_exc()
            continue


def static_roles_list(user, company_workflow):
    """ This is the list of roles that can't be changed using the single role
        add / remove
    """

    roles = [
        'Admin',
        'Admin config',
        'Employee',
        'Clients',
        'Config',
        'Manager',
        'Analytics',
        'Cash out',
        'Sales bags',
        'Sales delivery',
        'Sales checkout',
        'Page layout',
    ]
    current_card = constants.WORKFLOW_DATA[company_workflow].card(
        user.access_card_index
    )
    for role in current_card.groups():
        roles.append(role)

    return roles


def extra_roles_query(user, company_workflow):
    db = current.db

    query = (db.auth_group.role.like('Store%'))
    for role in static_roles_list(user, company_workflow):
        query |= db.auth_group.role == role

    return ~(query)
