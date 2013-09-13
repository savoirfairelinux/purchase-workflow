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
        'crates': fields.integer('Crates'),
    }


class stock_truck(orm.Model):

    _name = 'stock.truck'
    _description = 'Incoming truck'
    
    def action_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        truck = self.browse(cr, uid, ids, context=context)[0]
        picking = self.pool.get('stock.picking')
        picking_in = self.pool.get('stock.picking.in')
        move = self.pool.get('stock.move')
        prodlot_pool = self.pool.get('stock.production.lot')
        
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

        locations = self.pool.get('stock.location')
        suppliers_location = locations.search(cr, uid, [('name', '=', 'Suppliers')])[0]
        stock_location = locations.search(cr, uid, [('name', '=', 'Stock')])[0]

        for po in truck.purchase_order_ids:
            partial_data = {'delivery_date': truck.arrival}

            for po_line, count in products[po.id].itervalues():
                lot = po_line.account_analytic_id.code
                prodlot_id = prodlot_pool.search(cr, uid, [('name', '=', lot)])[0]

                picking_in_id = picking_in.search(
                        cr, uid, [('purchase_id', '=', po.id)], context=context)[0]
                existing_picking = picking.browse(cr, uid, picking_in_id, context=context)

                seq = existing_picking.name
                picking_id = existing_picking.id
                
                move_id = move.create(cr, uid, {
                    'name': seq,
                    'product_id': po_line.product_id.id,
                    'product_qty': count,
                    'product_uom': 1,
                    'prodlot_id': prodlot_id,
                    'location_id': suppliers_location,
                    'location_dest_id': stock_location,
                    'picking_id': picking_id,
                }, context=context)
                
                move.action_confirm(cr, uid, [move_id], context)
                partial_data['move%s' % (move_id, )] = {
                    'product_id': po_line.product_id.id,
                    'product_qty': count,
                    'product_uom': 1,
                    'prodlot_id': prodlot_id,
                }

            picking.do_partial(cr, uid, [picking_id], partial_data, context=context)

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
