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
import logging

_logger = logging.getLogger(__name__)


class sale(orm.Model):

    _inherit = 'sale.order.line'

    def _get_min_max_avg(self, cr, uid, ids, fields, args, context=None):
        context = context or {}

        res = {}

        analytic_account_pool = self.pool.get('account.analytic.account')

        for line in self.browse(cr, uid, ids, context=context):
            account_id = line.product_id.account_id
            res[line.id] = {
                'minimum': 0.0,
                'average': 0.0,
                'maximum': 0.0
            }

            if account_id:
                query = [
                    ('parent_id', '=', account_id.id),
                    ('total_in_qty', '!=', 0)
                ]
                child_ids = analytic_account_pool.search(
                    cr, uid, query, context=context)

                if child_ids:
                    values = analytic_account_pool.read(
                        cr, uid, child_ids,
                        ['estimated_tcu', 'total_in_qty'], context=context)
                    res[line.id]['minimum'] = min(
                        [v['estimated_tcu'] for v in values])

                    res[line.id]['maximum'] = max(
                        [v['estimated_tcu'] for v in values])

                    average = sum(
                        [v['estimated_tcu'] * v['total_in_qty']
                         for v in values])
                    if average:
                        res[line.id]['average'] = average / sum(
                            [v['total_in_qty'] for v in values])
                    else:
                        res[line.id]['average'] = 0

        return res

    def _get_purchase_order_line_ids(self, cr, uid, ids, context=None):
        context = context or {}

        res = []

        so_line_pool = self.pool.get('sale.order.line')

        for line in self.pool.get('purchase.order.line').browse(
                cr, uid, ids, context=context):
            if line.account_analytic_id:
                query = [
                    ('product_id.account_id.id', '=',
                     line.account_analytic_id.parent_id.id),
                    ('state', 'not in', ['done', 'cancel'])
                ]
                res += so_line_pool.search(cr, uid, query, context=context)

        return res

    def _get_account_analytic_account_ids(self, cr, uid, ids, context=None):
        context = context or {}

        res = []

        so_line_pool = self.pool.get('sale.order.line')

        for line in self.pool.get('account.analytic.account').browse(
                cr, uid, ids, context=context):
            query = [
                ('product_id.account_id.id', '=',
                 line.parent_id.id),
                ('state', 'not in', ['done', 'cancel'])
            ]
            res += so_line_pool.search(cr, uid, query, context=context)

        return res

    def _get_stock_production_lot_ids(self, cr, uid, ids, context=None):
        context = context or {}

        res = []

        so_line_pool = self.pool.get('sale.order.line')

        for lot in self.pool.get('stock.production.lot').browse(
                cr, uid, ids, context=context):
            query = [
                ('product_id.account_id.id', '=',
                 lot.account_analytic_id.parent_id.id),
                ('state', 'not in', ['done', 'cancel'])
            ]

            res += so_line_pool.search(
                cr, uid, query, context=context)

        return res

    _columns = {
        'minimum': fields.function(
            _get_min_max_avg,
            string='Min.',
            type='float',
            multi=True,
            store={
                'sale.order.line': (lambda self, cr, uid, ids, context: ids,
                                    ['product_id', 'price_unit'],
                                    10),
                'purchase.order.line': (_get_purchase_order_line_ids,
                                        ['account_analytic_id'],
                                        10),
                'stock.production.lot': (_get_stock_production_lot_ids,
                                         ['account_analytic_id'],
                                         10)
            }),
        'average': fields.function(
            _get_min_max_avg,
            string='Avg.',
            type='float',
            multi=True,
            store={
                'sale.order.line': (lambda self, cr, uid, ids, context: ids,
                                    ['product_id', 'price_unit'],
                                    10),
                'purchase.order.line': (_get_purchase_order_line_ids,
                                        ['account_analytic_id'],
                                        10),
                'stock.production.lot': (_get_stock_production_lot_ids,
                                         ['account_analytic_id'],
                                         10)
            }),
        'maximum': fields.function(
            _get_min_max_avg,
            string='Max.',
            type='float',
            multi=True,
            store={
                'sale.order.line': (lambda self, cr, uid, ids, context: ids,
                                    ['product_id', 'price_unit'],
                                    10),
                'purchase.order.line': (_get_purchase_order_line_ids,
                                        ['account_analytic_id'],
                                        10),
                'stock.production.lot': (_get_stock_production_lot_ids,
                                         ['account_analytic_id'],
                                         10)

            })
    }
