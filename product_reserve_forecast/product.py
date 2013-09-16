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

import openerp.addons.decimal_precision as dp
from openerp.osv import orm, fields

class product_product(orm.Model):

    _inherit = 'product.product'

    def _virtual_available(self, cr, uid, ids, names, arg, context=None):
        orig = self._product_available(cr, uid, ids, names, arg, context=context)
        product_pool = self.pool.get('product.product')
        for product_id in orig.keys():
            reserved = product_pool.browse(cr, uid, product_id, context=context).reserved
            orig[product_id]['virtual_available'] -= reserved

        return orig

    def _virtual_clone(self, cr, uid, ids, names, arg, context=None):
        '''Small hack to get priority over the Stock module's virtual_available'''

        res = {}

        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.virtual_available

        return res

    _columns = {
        'reserved': fields.integer('Reserved Quantity'),

        'virtual_clone':
            fields.function(_virtual_clone, type='float',
                digits_compute=dp.get_precision('Product Unit of Measure'), string='Forecasted Quantity'),

        'virtual_available': fields.function(_virtual_available, multi='qty_available',
            type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Forecasted Quantity',
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing - Reserved + Incoming)\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored in this location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
    }
