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

import sys
from gluon import current, URL
import constants


def main(email):
    import settup

    # this will create the system required payment methods, like stripe and wallet
    settup.create_payment_methods()
    settup.create_groups()
    settup.settup_mx()

    create_admin_url = URL(
        'user', 'create_admin_user', hmac_key=CONF.take('hmac.key'), host=True
    )
    mail = auth.settings.mailer
    mail.send(
        email,
        'Su punto de venta esta listo!',
        'Su punto de venta esta listo para ser usado, ingrese a {app_url}, para crear un usuario y comenzar a usar el sistema'
        .format(
            app_url=create_admin_url
        )
    )


if __name__ == "__main__":
    main(sys.argv[1])
