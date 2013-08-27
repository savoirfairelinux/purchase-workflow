# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# NOTE: The name of the supplied field was initially "display_name", but it seems that OpenERP,
# whenever it seems "name" in the field, returns the value for "name". Well...

{
    'name': 'Pallet delivery',
    'version': '1.1',
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'category': 'warehouse',
    'description': """

Lets you manage truck deliveries 
===========================================================

This module lets you specify where exactly in the delivery truck
was the merchandise.

Also lets you give more specific information like the temperature
at various points.

""",
    'depends': ['base', 'purchase', 'landed_cost_per_pallet', 'stock'],
    'data': [
        'stock_workflow.xml',
        'pallet_delivery_data.xml',
        'pallet_delivery.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'active': False,
}
