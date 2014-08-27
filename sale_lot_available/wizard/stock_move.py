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

from collections import defaultdict

from openerp.osv import fields, orm

class stock_production_lot(orm.Model):

    _inherit = 'stock.production.lot'

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        # Only override regular behaviour if on stock split wizard
        view_id = self.fields_view_get(cr, uid)['view_id']
        view = self.pool.get('ir.ui.view').browse(cr, uid, view_id, context=context)
        if view.model != 'stock.production.lot':
            return super(stock_production_lot, self).name_get(cr, uid, ids, context=context)

        if isinstance(ids, (int, long)):
            ids = [ids]

        if not context.has_key('available'):
            return super(stock_production_lot, self).name_get(cr, uid, ids, context=context)

        entered = defaultdict(lambda: 0.0)
        """
        if not ids:
            return []

        # ignore ids, redo the research to get all the product
        # ignore negative stock_available
        product_id = self.read(cr, uid, ids[0], context=context)['product_id'][0]
        ids = self.search(cr, uid, [['product_id', '=', product_id], ['stock_available', '>', 0]], context=context)

        for line in context['lines']:
            values = line[2]
            entered[values['prodlot_id']] += values['quantity']
        """

        res = []
        limit = 10
        count_limit = 0
        move_lines_obj = self.pool.get('stock.move')
        for lot in self.browse(cr, uid, ids, context=context):
            # remove other draft stock.move prodlot
            move_lines_ids = move_lines_obj.search(cr, uid, [('prodlot_id', '=', lot.id)], context=context)
            move_lines = move_lines_obj.browse(cr, uid, move_lines_ids, context=context)
            other_qty = sum([move.product_qty for move in move_lines if move.state in ['draft', 'waiting', 'confirmed', 'assigned']])
            net_available = lot.stock_available - entered[lot.id] - other_qty
            if count_limit >= limit:
                break
            """
            if net_available > 0:
                count_limit += 1
                res.append((lot.id, '%s / %.2f' % (lot.name, net_available)))
            """
            res.append((lot.id, '%s / %.2f' % (lot.name, net_available)))

        return res
