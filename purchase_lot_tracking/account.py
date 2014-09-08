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
import openerp.addons.decimal_precision as dp


class account_analytic_account(orm.Model):

    _inherit = 'account.analytic.account'

    def _calculate_total_in(self, cr, uid, ids, name, arg, context=None):
        res = {}

        move_pool = self.pool.get('stock.move')

        for account in self.browse(cr, uid, ids):
            res[account.id] = 0.0
            total_moves = 0
            production_pool = self.pool.get('stock.production.lot')
            lot_ids = production_pool.search(cr, uid, [('name', '=', account.name)])

            for lot in production_pool.browse(cr, uid, lot_ids):
                move_ids = move_pool.search(
                    cr, uid, [('prodlot_id', '=', lot.id)])
                for move in move_pool.browse(cr, uid, move_ids):

                    # Add in purchases, remove sales
                    if move.type == 'in':
                        total_moves += move.product_qty
                    #else:
                    #    total_moves -= move.product_qty

            total_moves = max(total_moves, 0)
            res[account.id] = total_moves

        return res

    def _get_stock_move_ids(self, cr, uid, ids, context=None):
        context = context or {}

        res = []

        analytic_account_pool = self.pool.get('account.analytic.account')

        for move in self.pool.get('stock.move').browse(
                cr, uid, ids, context=context):
            if move.prodlot_id:
                query = [('code', '=', move.prodlot_id.name)]

                res += analytic_account_pool.search(
                    cr, uid, query, context=context)

        return res

    def _calculate_tcu(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for account in self.browse(cr, uid, ids):
            res[account.id] = 0.0
            if account.total_in_qty > 0:
                res[account.id] = account.credit / account.total_in_qty
        return res

    def _estimated_tcu(self, cr, uid, ids, name, arg, context=None):
        res = {}
        po_line_pool = self.pool.get('purchase.order.line')
        for line in self.browse(cr, uid, ids):
            if line.code.startswith('LOT'):
                po_line_ids = po_line_pool.search(cr, uid, [('account_analytic_id', '=', line.id)])
                if po_line_ids:
                    po_line_id = po_line_ids[0]
                    po_line = po_line_pool.browse(cr, uid, po_line_id, context)
                    if po_line.product_qty == 0:
                        res[line.id] = 0
                    else:
                        res[line.id] = po_line.landed_costs / po_line.product_qty
                else:
                    res[line.id] = 0.0
            else:
                res[line.id] = 0.0
        return res

    _columns = {
        'purchase_order': fields.many2one(
            'purchase.order',
            'Purchase Order',
            help='Issuing Purchase Order'),
        'total_cost_unit': fields.function(
            _calculate_tcu,
            string='Total Cost Unit',
            type='float'),
        'total_in_qty': fields.function(
            _calculate_total_in,
            string='Total Received Quantity',
            type='float',
            store={
                'stock.move': (_get_stock_move_ids,
                               ['product_qty'],
                               10)
            }),
        'estimated_tcu': fields.function(
            _estimated_tcu,
            string='Estimated Total Cost per Unit',
            type='float'),
    }
