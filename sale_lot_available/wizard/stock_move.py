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

        for line in context['lines']:
            values = line[2]
            entered[values['prodlot_id']] += values['quantity']

        res = []

        for lot in self.browse(cr, uid, ids, context=context):
            net_available = lot.stock_available - entered[lot.id]
            res.append((lot.id, '%s / %.2f' % (lot.name, net_available)))

        return res

if 0:
    class stock_move_split_lines(orm.TransientModel):

        _inherit = 'stock.move.split.lines'

        def _prodlot_id(self, cr, uid, ids, name, arg, context=None):
            import ipdb; ipdb.set_trace()
            if context is None:
                context = {}

            res = {}

            for thing in self.browse(cr, uid, ids, context=context):
                res[thing.id] = 'thing %d' % (thing.id, )

            return res

        def _prodlot_id_inv(self, cr, uid, ids, name, value, arg, context=None):
            import ipdb; ipdb.set_trace()
            return True

        def _prodlot_id_search(self, cr, uid, obj, name, arg, context=None):
            import ipdb; ipdb.set_trace()
            return [('id', 'in', [1])]

        _columns = {
            'prodlot_id': fields.function(
                _prodlot_id,
                fnct_inv=_prodlot_id_inv,
                type='many2one',
                fnct_search=_prodlot_id_search,
                method=True,
                store=True,
                string='Serial Number'),
        }
