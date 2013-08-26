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

def group(lst):
    if not lst:
        return []

    res = []
    current = lst[0]

    grp = []
    for x in lst:
        if x != current:
            res.append(grp)
            grp = []
        grp.append(x)
        current = x

    if grp:
        res.append(grp)

    return res


def dbg(thing):
    print('\033[1;31m%r\033[0m' % (thing, ))  # ]]


class purchase_order_line(orm.Model):

    _inherit = 'purchase.order.line'

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        dbg('context: %r' % (context, ))

        if not context.has_key('nice'):
            res = []

            for line in self.browse(cr, uid, ids, context=context):
                nice = '%s / %s' % (line.name, line.account_analytic_id.code)
                res.append((line.id, nice))

            return res

        res = []

        parent = context['parent']
        all_pallets = parent['left_pallet_ids'] + parent['right_pallet_ids']
        po_ids = parent['purchase_order_ids'][0][2]

        po_pool = self.pool.get('purchase.order.line')
        pallet_ids = []

        for pallet_struct in all_pallets:
            if pallet_struct[0] == 4:
                # Already there values

                thing = po_pool.browse(cr, uid, pallet_struct[1], context=context)
                if thing.left_pallet:
                    pallet_ids.append(left_pallet)
                else:
                    pallet_ids.append(right_pallet)

            else:
                # New values

                pallet_ids.extend(list(pallet_struct[2].values()))

        pallet_ids = dict((x[0], len(x)) for x in group(sorted(pallet_ids)))

        dbg('pallet_ids: %r' % (pallet_ids, ))

        po_line_ids = po_pool.search(cr, uid, [('order_id', 'in', po_ids)], context=context)
        po_lines = po_pool.browse(cr, uid, po_line_ids, context=context)

        for line in po_lines:
            try:
                this_count = pallet_ids[line.id]
            except KeyError:
                this_count = 0

            if this_count < line.nb_pallets:
                nice = '%s / %s' % (line.name, line.account_analytic_id.code)
                res.append((line.id, nice))

        return res


class purchase_order(orm.Model):

    _inherit = 'purchase.order'

    _columns = {
        'stock_truck_ids': fields.many2many(
            'stock.truck', 'truck_order_rel', 'order_id', 'truck_id', 'Trucks'),
    }


class stock_truck_line(orm.Model):

    _name = 'stock.truck.line'
    _description = 'A single pallet shipped in an incoming truck'

    _columns = {
        'name': fields.char('Name', size=64),
        'left_id': fields.many2one('stock.truck', 'Truck'),
        'right_id': fields.many2one('stock.truck', 'Truck'),
        'pallet': fields.many2one('purchase.order.line', 'Pallet'),
    }


class stock_truck(orm.Model):

    _name = 'stock.truck'
    _description = 'Incoming truck'
    
    def action_done(self, cr, uid, ids, context=None):
        pass

    _columns = {
        'name': fields.char('Name', size=64),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State', readonly=True, select=True, track_visibility='onchange'),
        'front_temperature': fields.float('Front Temperature'),
        'back_temperature': fields.float('Back Temperature'),
        'truck_sn': fields.char('Truck S/N', size=64),
        'supplier': fields.many2one('res.partner', 'Supplier'),
        'arrival': fields.date('Date of Arrival'),
        'purchase_order_ids': fields.many2many(
            'purchase.order', 'truck_order_rel', 'truck_id', 'order_id', 'Purchase Orders'),
        'left_pallet_ids': fields.one2many('stock.truck.line', 'left_id', 'Pallets'),
        'right_pallet_ids': fields.one2many('stock.truck.line', 'right_id', 'Pallets'),
    }

    _defaults = {
        'name': lambda self, cr, uid, ctx={}: self.pool.get('ir.sequence').get(cr, uid, 'stock.truck'),
    }
