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

    def get_profit_all(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'profit_po': 0.0,
                'amount_total_discount': 0.0,
                'amount_landing_cost': 0.0,
                'amount_total_price_unit': 0.0,
                'amount_total_sale_order': 0.0
            }
            total_landed_cost_po = 0.0
            if line.landed_cost_line_ids:
                for costs in line.landed_cost_line_ids:
                    total_landed_cost_po += costs.amount
            res[line.id]['amount_landing_cost'] = total_landed_cost_po
            total_price_unit = 0.0

            amount_total_sale_order = 0.0
            amount_total_discounts = 0.0
            total_landed_cost_so = 0.0
            if line.order_line:
                for one_line in line.order_line:
                    acc_id = one_line.account_analytic_id.id
                    total_price_unit += one_line.price_unit
                    ids_stock_prod_lot = self.pool.get('stock.production.lot').search(cr, uid, [('account_analytic_id', '=', acc_id)], context=context)[0]
                    id_stock_prod_lot = self.pool.get('stock.production.lot').browse(cr, uid, ids_stock_prod_lot).id
                    stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('prodlot_id', '=', id_stock_prod_lot)], context=context)

                    list_stock_move = self.pool.get('stock.move').browse(cr, uid, stock_move_ids, context)
                    amount_total_sale_order = 0.0
                    amount_total_discounts = 0.0
                    if list_stock_move:
                        for one_move_line in list_stock_move:
                            if one_move_line.picking_id.sale_id:
                                amount_total_sale_order += one_move_line.picking_id.sale_id.amount_total
                                amount_total_discounts += one_move_line.picking_id.sale_id.amount_total * (1-(one_move_line.picking_id.sale_id.partner_id.discount or 0.0))
                                total_landed_cost_so = 0.0
                                if one_move_line.picking_id.sale_id.landed_cost_line_ids:
                                    for costs_so in one_move_line.picking_id.sale_id.landed_cost_line_ids:
                                        total_landed_cost_so += costs_so.amount
            res[line.id]['total_landed_cost_so'] = total_landed_cost_so
            res[line.id]['amount_total_price_unit'] = total_price_unit
            res[line.id]['amount_total_discount'] = amount_total_discounts
            res[line.id]['amount_total_sale_order'] = amount_total_sale_order
            res[line.id]['profit_po'] = res[line.id]['amount_total_sale_order'] - (res[line.id]['total_landed_cost_so'] + res[line.id]['amount_total_price_unit'] + res[line.id]['amount_total_discount'] + res[line.id]['amount_landing_cost'])
        return res


    _columns = {
        'profit_po': fields.function(
            get_profit_all,
            digits_compute=dp.get_precision('Account'),
            string='Profit', multi='all'),
        'amount_total_discount': fields.function(
            get_profit_all,
            digits_compute=dp.get_precision('Account'),
            string='Total amount discount', multi='all'),
        'amount_landing_cost': fields.function(
            get_profit_all,
            digits_compute=dp.get_precision('Account'),
            string='Total amount landing cost', multi='all'),
        'amount_total_price_unit': fields.function(
            get_profit_all,
            digits_compute=dp.get_precision('Account'),
            string='Total amount price unit', multi='all'),
        'amount_total_sale_order': fields.function(
            get_profit_all,
            digits_compute=dp.get_precision('Account'),
            string='Total amount sale order', multi='all'),
        'total_landed_cost_so': fields.function(
            get_profit_all,
            digits_compute=dp.get_precision('Account'),
            string='Total amount landing cost sale order', multi='all'),
    }


