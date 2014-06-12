# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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


class sale_order(orm.Model):
    """Adding landed costs per pallet"""
    _inherit = 'sale.order'

    def _landed_cost_base_pallet(self, cr, uid, ids, name, args, context):
        """Calculate total of landed costs per pallet"""
        ret = {}
        for line in self.browse(cr, uid, ids):
            ret[line.id] = sum(costs.amount for costs in line.landed_cost_line_ids if costs.price_type == 'per_pallet')
        return ret

    _columns = {
        'landed_cost_base_pallet': fields.function(_landed_cost_base_pallet,
                                                   digits_compute=dp.get_precision('Account'),
                                                   string='Landed Costs Base Pallet'),
    }


class sale_order_line(orm.Model):
    """Add pallet information to sale order lines"""
    _inherit = 'sale.order.line'

    def _product_quantity(self, cursor, user, ids, name, arg, context=None):
        """Calculate quantity if there are pallets and crates per pallet"""
        ret = {}
        for line in self.browse(cursor, user, ids, context=context):
            ret[line.id] = (line.nb_crates_per_pallet or 0) * (line.nb_pallets or 0)
        return ret

    def _landing_cost_order(self, cr, uid, ids, name, args, context):
        """Compute Landing costs including palet costs"""
        ret = super(sale_order_line, self)._landing_cost_order(cr, uid, ids, name, args, context)
        lines = self.browse(cr, uid, ids)
        # Pre-compute total number of pallets
        pallets_total = sum(line.nb_pallets for line in lines if line.order_id.landed_cost_line_ids)
        # Landed costs line by line
        for line in lines:
            if line.order_id.landed_cost_line_ids and pallets_total:
                ret[line.id] += line.order_id.landed_cost_base_pallet/pallets_total * line.nb_pallets
        return ret

    _columns = {
        'nb_pallets': fields.float('Pallets', required=True),
        'nb_crates_per_pallet': fields.integer('Crates per pallet', required=True),
        'product_uom_qty': fields.function(_product_quantity,
                                           digits_compute=dp.get_precision('Product Unit of Measure'),
                                           string="Quantity",
                                           type='float'),
        'landing_costs_order': fields.function(_landing_cost_order,
                                               digits_compute=dp.get_precision('Account'),
                                               string='Landing Costs from Order'),
    }


class landed_cost_position(orm.Model):
    """Add price types"""
    _inherit = 'landed.cost.position'
    _columns = {
        'price_type': fields.selection([('per_pallet', 'Per Pallet'),
                                        ('per_unit', 'Per Quantity'),
                                        ('value', 'Absolute Value')],
                                       'Amount Type',
                                       required=True,
                                       help="""\
Defines if the amount is to be calculated for each quantity or an absolute value"""),
    }
    _defaults = {
        'price_type': 'per_pallet',
    }
