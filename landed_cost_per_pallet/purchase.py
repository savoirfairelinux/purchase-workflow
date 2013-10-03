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

class purchase_order(orm.Model):

    _inherit = 'purchase.order'

    def _landed_cost_base_pallet(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}

        result = {}
        landed_costs_base_pallet = 0.0

        for line in self.browse(cr, uid, ids):
            if line.landed_cost_line_ids:
                for costs in line.landed_cost_line_ids:
                    if costs.price_type == 'per_pallet':
                        landed_costs_base_pallet += costs.amount
            result[line.id] = landed_costs_base_pallet

        return result

    _columns = {
        'landed_cost_base_pallet': fields.function(
            _landed_cost_base_pallet,
            digits_compute=dp.get_precision('Account'),
            string='Landed Costs Base Pallet'),
    }


class purchase_order_line(orm.Model):

    _inherit = 'purchase.order.line'

    def _product_quantity(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cursor, user, ids, context=context):
            if not line.nb_crates_per_pallet or not line.nb_pallets:
                res[line.id] = 0
            else:
                res[line.id] = line.nb_crates_per_pallet * line.nb_pallets
        return res

    def _landing_cost_order(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}

        result = {}

        lines = self.browse(cr, uid, ids)

        # Pre-compute total number of pallets
        pallets_total = 0.0
        for line in lines:
            if line.order_id.landed_cost_line_ids:
                pallets_total += line.nb_pallets

        # Landed costs line by line
        for line in lines:
            landed_costs = 0.0
            # distribution of landed costs of PO
            if line.order_id.landed_cost_line_ids:
                # Base value (Absolute Value)
                landed_costs += line.order_id.landed_cost_base_value / line.order_id.amount_total * line.price_subtotal

                # Base quantity (Per Quantity)
                landed_costs += line.order_id.landed_cost_base_quantity / line.order_id.quantity_total * line.product_qty

                # Base pallet (Per Pallet)
                landed_costs += line.order_id.landed_cost_base_pallet / pallets_total * line.nb_pallets
            result[line.id] = landed_costs

        return result

    _columns = {
        'nb_pallets': fields.integer('Pallets', required=True),
        'nb_crates_per_pallet': fields.integer('Crates per pallet', required=True),
        'product_qty': fields.function(_product_quantity, string="Quantity", type='float'),
        'landing_costs_order' : fields.function(_landing_cost_order, digits_compute=dp.get_precision('Account'), string='Landing Costs from Order'),
    }


class landed_cost_position(orm.Model):

    _inherit = 'landed.cost.position'

    _columns = {
        'price_type': fields.selection(
            [('per_pallet', 'Per Pallet'), ('per_unit','Per Quantity'), ('value','Absolute Value')],
            'Amount Type',
            required=True,
            help="Defines if the amount is to be calculated for each quantity or an absolute value"),
    }

    _defaults = {
        'price_type': 'per_pallet',
    }
