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

from openerp.osv import orm, fields

def group(lst):
    '''Saner group function than the one found in itertools

    This one mimics Haskell's group from Data.List:
        group :: Eq a => [a] -> [[a]]
    '''

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


class purchase_order_line(orm.Model):

    _inherit = 'purchase.order.line'

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

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

        stl_pool = self.pool.get('stock.truck.line')
        pallet_ids = []

        crates = defaultdict(lambda: 0)
        for pallet_struct in all_pallets:
            if pallet_struct[0] == 4:
                st_line = stl_pool.browse(cr, uid, pallet_struct[1], context=context)
                crates[st_line.pallet.id] += st_line.crates
            else:
                fields = pallet_struct[2]
                crates[fields['pallet']] += fields['crates']

        po_line_ids = self.search(cr, uid, [('order_id', 'in', po_ids)], context=context)
        po_lines = self.browse(cr, uid, po_line_ids, context=context)

        for line in po_lines:
            total_crates = line.nb_pallets * line.nb_crates_per_pallet
            available = max(0, total_crates - crates[line.id])

            nice = '%s / %s (%d)' % (line.name, line.account_analytic_id.code, available)
            res.append((line.id, nice))

        return res


class purchase_order(orm.Model):

    _inherit = 'purchase.order'

    def _assigned(self, cr, uid, obj, name, args, context=None):
        '''Domain filter on corresponding entries in stock.picking where state is assigned'''

        if context is None:
            context = {}

        import ipdb; ipdb.set_trace()

        picking_pool = self.pool.get('stock.picking')
        ids = picking_pool.search(cr, uid, [('state', '=', 'assigned')], context=context)
        po_ids = [po.purchase_id.id for po in picking_pool.browse(cr, uid, ids, context=context)]

        return [('id', 'in', po_ids)]

    _columns = {
        'stock_truck_ids': fields.many2many(
            'stock.truck', 'truck_order_rel', 'order_id', 'truck_id', 'Trucks'),
        'assigned': fields.function(lambda **x: True, fnct_search=_assigned, type='boolean', method=True),
    }


class stock_truck_line(orm.Model):

    _name = 'stock.truck.line'
    _description = 'A single pallet shipped in an incoming truck'

    _columns = {
        'name': fields.char('Name', size=64),
        'left_id': fields.many2one('stock.truck', 'Truck'),
        'right_id': fields.many2one('stock.truck', 'Truck'),
        'pallet': fields.many2one('purchase.order.line', 'Pallet'),
        'crates': fields.integer('Crates'),
    }


class stock_truck(orm.Model):

    _name = 'stock.truck'
    _description = 'Incoming truck'
    
    def action_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        truck = self.browse(cr, uid, ids, context=context)[0]

        # Build a dictionary of:
        #   - key: Purchase Order
        #   - value: a dictionary of:
        #       - key: Lot Number
        #       - value: tuple of
        #         - Purchase Order Line
        #         - Crate count
        products = {}

        def _process_pallets(column):
            for line in column:
                po = line.pallet.order_id
                lot = line.pallet.account_analytic_id.code

                if not products.has_key(po.id):
                    products[po.id] = {}

                if not products[po.id].has_key(lot):
                    products[po.id][lot] = (line.pallet, 0)

                count = products[po.id][lot][1]
                products[po.id][lot] = (products[po.id][lot][0], count + line.crates)

        _process_pallets(truck.left_pallet_ids)
        _process_pallets(truck.right_pallet_ids)

        # Make the calls to the Pickings stock moves

        picking_pool = self.pool.get('stock.picking')
        move_pool = self.pool.get('stock.move')

        for po in truck.purchase_order_ids:
            partial_data = {'delivery_date': truck.arrival}

            picking_id = picking_pool.search(
                    cr, uid,
                    ['&', ('purchase_id', '=', po.id), ('state', '=', 'assigned')],
                    context=context)[0]

            for po_line, count in products[po.id].itervalues():
                move_id = move_pool.search(
                        cr, uid,
                        ['&', ('picking_id', '=', picking_id), ('purchase_line_id', '=', po_line.id)],
                        context=context)[0]

                prodlot_id = move_pool.browse(cr, uid, move_id, context=context).prodlot_id.id

                partial_data['move%s' % (move_id, )] = {
                    'product_id': po_line.product_id.id,
                    'product_qty': count,
                    'product_uom': 1,
                    'prodlot_id': prodlot_id,
                }

            picking_pool.do_partial(cr, uid, [picking_id], partial_data, context=context)

        self.write(cr, uid, ids, {'state': 'done'})

        return True

    _columns = {
        # Overhead
        'name': fields.char('Name', size=64),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State', readonly=True, select=True, track_visibility='onchange'),

        # Display
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
        'state': 'draft',
    }
