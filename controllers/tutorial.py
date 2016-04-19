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


class TutorialStep:
    def __init__(self, title, help_text, function):
        self.title = title
        self.help_text = help_text
        self.function = function

    def call(self):
        return self.function()


def step_1_1():
    """ Address settup """

    form = SQLFORM(db.address)
    if form.process().accepted:
        redirect(URL('step', args=[1, 2], vars=dict(id_address=form.vars.id)))
    elif form.errors:
        response.flash = T('Something is wrong')
    return dict(form=form)


def step_1_2():
    """ Store settup
        vars [id_address]
    """
    form = SQLFORM(db.store)
    form.vars.id_address = request.vars.id_address
    if form.process().accepted:
        # insert store group
        db.auth_group.insert(role='Store %s' % form.vars.id)
        response.flash = T('form accepted')
        redirect(URL('step', args=[1, 3]))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


def step_1_3():
    """ Employee settup """

    # session._next = URL('step', args=[1, 4])
    redirect(URL('user', 'create', vars=dict(_next=URL('step', args=[1, 4]))))



stages = [
    {
        'title': 'Store configuration',
        'help_text': '',
        'steps': [
            TutorialStep('Address creation', '', step_1_1),
            TutorialStep('Store creation', '', step_1_2),
            TutorialStep('Store creation', '', step_1_3)
        ]
    }
]


# def start():
#     session._next = URL('store', 'create')
#     redirect(URL('address', 'create'))


@auth.requires_membership('Admin')
def step():
    """
        args: [stage, step]
    """

    stage_index = int(request.args(0)) - 1
    step_index = int(request.args(1)) - 1

    stage = stages[stage_index]
    step = stage['steps'][step_index]
    step_locals = step.call()

    return dict(title=stage['title'], help_text=stage['help_text'], step=step, **step_locals)


@auth.requires_membership('Admin')
def index():
    return dict()
