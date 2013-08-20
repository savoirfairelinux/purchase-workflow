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

from openerp.osv import orm, fields

class purchase_order_middleman(orm.Model):

    '''Acts as a broker between a 'stock.truck.line' and a 'product.order.line'.

    The middleman bridges a many2one between a truck and a PO. The field could
    be a simple `fields.many2one()`, but we need to customise the way the PO
    line is displayed by having it record not only the product name, but also
    the tracking lot number.

    Thus, this model's existence is centered around a `name_get()` override.
    '''

    _name = 'purchase.order.middleman'

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        res = []
        po_pool = self.pool.get('purchase.order.line')
        po_line_ids = po_pool.search(cr, uid, [], context=context)
        po_lines = po_pool.browse(cr, uid, po_line_ids, context=context)

        for line in po_lines:
            nice = '%s / %s' % (line.name, line.account_analytic_id.code)
            res.append((line.id, nice))

        return res

    _columns = {
        'name': fields.char('Name', size=64),
        'purchase_order_line_ids': fields.many2one('purchase.order.line', 'Line'),
    }


class purchase_order(orm.Model):

    _inherit = 'purchase.order'

    _columns = {
        'stock_truck_ids': fields.many2many(
            'stock.truck', 'truck_order_rel', 'order_id', 'truck_id', 'Trucks'),
    }


class stock_truck_line(orm.Model):

    _name = 'stock.truck.line'

    def _get_lot_and_product(self, cr, uid, ids, name, arg, context=None):
        res = {}

        print('AAAAAAURGH!')

        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {'lot_and_product': 'poulet'}

        return res

    def _set_lot_and_product(self, cr, uid, ids, name, value, arg, context=None):
        # TODO

        return True

    _columns = {
        'name': fields.char('Name', size=64),
        'truck_id': fields.many2one('stock.truck', 'Truck'),
        'left_pallet': fields.many2one('purchase.order.middleman', 'Middleman'),
        'right_pallet': fields.function(_get_lot_and_product, fnct_inv=_set_lot_and_product, type='many2one', obj='purchase.order.line', store=True, string='Right Pallet'),
    }


class stock_truck(orm.Model):

    _name = 'stock.truck'

    _columns = {
        'name': fields.char('Name', size=64),
        'front_temperature': fields.float('Front Temperature'),
        'back_temperature': fields.float('Back Temperature'),
        'truck_sn': fields.char('Truck S/N', size=64),
        'supplier': fields.many2one('res.partner', 'Supplier'),
        'arrival': fields.date('Date of Arrival'),
        'product_order_ids': fields.many2many(
            'purchase.order', 'truck_order_rel', 'truck_id', 'order_id', 'Purchase Orders'),
        'pallet_ids': fields.one2many('stock.truck.line', 'truck_id', 'Pallets'),
    }

    _defaults = {
        'name': lambda self, cr, uid, ctx={}: self.pool.get('ir.sequence').get(cr, uid, 'stock.truck'),
    }
