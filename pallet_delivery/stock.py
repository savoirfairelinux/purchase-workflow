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
from openerp.tools.translate import _
from openerp.osv import orm, fields

def group(lst):
    """Saner group function than the one found in itertools

    This one mimics Haskell's group from Data.List:
        group :: Eq a => [a] -> [[a]]
    """

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


class stock_move(orm.Model):

    _inherit = 'stock.move'

    def _find_hidden(self, cr, uid, ids, context=None):
        po_pool = self.pool.get("purchase.order")
        hidden_id = po_pool.search(cr, uid, [('hidden', '=', True)], context=context)[0]
        return po_pool.browse(cr, uid, hidden_id, context)

    @staticmethod
    def _unique_line(seq):
        seen = set()
        seen_add = seen.add
        return [ x for x in seq if x not in seen and not seen_add(x)]

    @staticmethod
    def _get_line_name(line, crates=None, force_total_qty=False):
        available = None
        nice = '%s' % line.product_id.name
        incoming_crates = line.product_qty
        if crates:
            # Incoming crates
            available = max(0, incoming_crates - crates[line.id])
        elif force_total_qty:
            available = incoming_crates

        nice += " / %s" % line.prodlot_id.name

        if available is not None:
            nice += " (%d)" % available

        return nice, available

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        stl_pool = self.pool.get('stock.truck.line')
        spi_pool = self.pool.get('stock.picking.in')
        # Out from selection; display name

        #hidden = self._find_hidden(cr, uid, ids, context=context)
        res = []
        if not context.has_key('nice'):
            for line in self.browse(cr, uid, ids, context=context):
                name, available = self._get_line_name(line)
                res.append((line.id, name))

            # Add special 'not ours' line
            #res.append((hidden.id, hidden.name))
            return res

        # Doing a selection
        # Add special 'not ours' line
        #res.append((hidden.id, hidden.name))

        # Retrieve entered form data
        parent = context['parent']
        all_pallets = parent['left_pallet_ids'] + parent['right_pallet_ids']
        po_ids = parent['purchase_order_ids'][0][2]

        # find list of stock picking in
        spi_ids = spi_pool.search(cr, uid, [('purchase_id', '=', po_ids)],
                                  context=context)

        # Build crate structure
        crates = defaultdict(lambda: 0)
        for pallet_struct in all_pallets:
            if pallet_struct[0] == 4:
                st_line = stl_pool.browse(cr, uid, pallet_struct[1],
                                          context=context)
                crates[st_line.pallet.id] += st_line.crates
            else:
                fields = pallet_struct[2]
                if fields and 'pallet' in fields:
                    crates[fields['pallet']] += fields['crates']

        spi_lines = spi_pool.browse(cr, uid, spi_ids, context=context)
        all_lines = [line for lines in spi_lines for line in lines.move_lines
                     if line.state == "assigned"]
        move_line = self._unique_line(all_lines)

        # Prettify data to be displayed
        for line in move_line:
            force_total_qty = not crates
            name, available = self._get_line_name(line, crates=crates,
                                                  force_total_qty=force_total_qty)
            if available:
                res.append((line.id, name))

        return res


class purchase_order(orm.Model):

    _inherit = 'purchase.order'

    def _assigned(self, cr, uid, obj, name, args, context=None):
        '''Domain filter on corresponding entries in stock.picking where state is assigned'''

        if context is None:
            context = {}

        picking_pool = self.pool.get('stock.picking')
        ids = picking_pool.search(cr, uid, [('state', '=', 'assigned')], context=context)
        po_ids = [po.purchase_id.id for po in picking_pool.browse(cr, uid, ids, context=context)]

        return [('id', 'in', po_ids)]

    _columns = {
        'hidden': fields.boolean('Hidden'),
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
        'pallet': fields.many2one('stock.move', 'Pallet', required=True),
        'crates': fields.integer('Crates', required=True),
    }


class stock_truck(orm.Model):

    _name = 'stock.truck'
    _description = 'Incoming truck'

    def onchange_arrival(self, cr, uid, ids, arrival, context=None):
        '''Force seconds to zero'''

        arrival = arrival[:-2] + '00'

        return {'value': {'arrival': arrival}}
    
    def action_done(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        truck = self.browse(cr, uid, ids, context=context)[0]

        # Build a dictionary of:
        #   - key: Purchase Order
        #   - value: a dictionary of:
        #     - key: Lot Number
        #     - value: tuple of
        #       - Purchase Order Line
        #       - Crate count
        products = defaultdict(dict)

        def _process_pallets(column):
            for line in column:
                pallet = line.pallet
                pi = pallet.picking_id
                po = pallet.purchase_line_id.order_id
                lot = pallet.prodlot_id if pallet.prodlot_id else None
                # Skip over fake 'not ours' line
                if po and po.hidden:
                    continue

                if not products[pi.id].has_key(lot):
                    products[pi.id][lot] = (pallet, 0)

                lot_product = products[pi.id][lot]
                count = lot_product[1]
                products[pi.id][lot] = (lot_product[0], count + line.crates)

        _process_pallets(truck.left_pallet_ids)
        _process_pallets(truck.right_pallet_ids)

        # Make the calls to the Pickings stock moves

        picking_pool = self.pool.get('stock.picking')

        for po in truck.purchase_order_ids:
            pi = None
            pi_ids = picking_pool.search(
                cr, uid,
                ['&', ('purchase_id', '=', po.id), ('state', '=', 'assigned')],
                context=context)
            if pi_ids:
                # take the last one
                pi = pi_ids[-1]

            if not pi or not products.has_key(pi):
                # Purchase Order was added to the list, but there are not
                # pallets pertaining to that PO.
                continue

            partial_data = {'delivery_date': truck.arrival}


            for move_line, count in products[pi].values():
                # Skip over the fake 'not ours' line
                po_line = move_line.purchase_line_id
                if po_line and po_line.order_id.hidden:
                    continue

                partial_data['move%s' % (move_line.id, )] = {
                    'product_id': move_line.product_id.id,
                    'product_qty': count,
                    'product_uom': 1,
                    'prodlot_id': move_line.prodlot_id.id,
                }

            picking_pool.do_partial(cr, uid, [pi], partial_data, context=context)

        self.write(cr, uid, ids, {'state': 'done'})

        return True

    @staticmethod
    def validate_temperature(cr, uid, ids, temperature, field_name,
                             context=None):
        try:
            float(temperature)
        except ValueError:
            warning = {'title': _('Input Error !'),
                       'message': _('Please enter real numbers.')}
            return {'value': {field_name: ""}, 'warning': warning}
        return True

    _columns = {
        # Overhead
        'name': fields.char('Name', size=64),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ], 'State', readonly=True, select=True, track_visibility='onchange'),

        # Display
        'front_temperature': fields.char('Front Temperature', required=True),
        'back_temperature': fields.char('Back Temperature', required=True),
        'truck_sn': fields.char('Truck S/N', size=64),
        'supplier': fields.many2one('res.partner', 'Supplier', required=True),
        'arrival': fields.datetime('Date of Arrival', required=True),
        'purchase_order_ids': fields.many2many(
            'purchase.order', 'truck_order_rel', 'truck_id', 'order_id', 'Purchase Orders'),
        'left_pallet_ids': fields.one2many('stock.truck.line', 'left_id', 'Pallets'),
        'right_pallet_ids': fields.one2many('stock.truck.line', 'right_id', 'Pallets'),
    }

    _defaults = {
        'name': lambda self, cr, uid, ctx={}: self.pool.get('ir.sequence').get(cr, uid, 'stock.truck'),
        'state': 'draft',
        'front_temperature': None,
    }
