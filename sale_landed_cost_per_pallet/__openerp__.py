# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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

{
    'name': 'Sale Landed Cost per Pallet',
    'version': '1.1',
    'author': 'Savoir-faire Linux',
    'maintainer': 'Savoir-faire Linux',
    'website': 'http://www.savoirfairelinux.com',
    'category': 'Generic Modules/Purchases',
    'description': """
Lets you manage product quantities using crates and pallets for sales
=====================================================================

This module modifies the sale module to let you manage product
quantities by specifying a number of pallets and a number of crates
per pallet.

This also adds a 'Per Pallet' option to landed costs, in order to compute the
landed costs per pallet.
""",
    'depends': ['base', 'sale_landed_costs', ],
    'external_dependencies': {},
    'data': ['sale_cost_per_pallet_view.xml', ],
    'demo': [],
    'test': [],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
