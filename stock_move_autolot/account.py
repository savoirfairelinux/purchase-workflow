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


class account_analytic_account(orm.Model):
    _inherit = 'account.analytic.account'

    def _estimated_tcu(self, cr, uid, ids, name, arg, context=None):
        # Pools
        stock_move_pool = self.pool.get('stock.move')
        po_line_pool = self.pool.get('purchase.order.line')

        def transformed_tcu():

            # Get the stock move id of the transformed product
            stock_move_id = stock_move_pool.search(cr, uid, [('prodlot_id.name', '=', line.code)], context=context)[0]
            stock_move = stock_move_pool.browse(cr, uid, stock_move_id, context=context)

            # Get the stock move id of the initial product
            # We can safely assume there is only one
            if not stock_move.production_id:
                return 0
            initial_stock_move = stock_move.production_id.move_lines2[0]
            initial_analytic_id = initial_stock_move.prodlot_id.account_analytic_id.id

            """Get parent_po_line and calculate price based on transformation"""
            parent_po_line_id = po_line_pool.search(cr, uid, [('account_analytic_id', '=', initial_analytic_id)], context=context)[0]
            parent_po_line = po_line_pool.browse(cr, uid, parent_po_line_id, context=context)

            # Calculate transformed price
            return parent_po_line.landed_costs / (parent_po_line.product_qty * stock_move.production_id.bom_id.product_qty)

        # Call super
        res = super(account_analytic_account, self)._estimated_tcu(cr, uid, ids, name, arg, context)
        for line in self.browse(cr, uid, ids):
            if line.code.startswith('LOT') and not po_line_pool.search(cr, uid, [('account_analytic_id', '=', line.id)]):
                res[line.id] = transformed_tcu()

        return res

    # Overwrite estimated_tcu
    _columns = {
        'estimated_tcu': fields.function(_estimated_tcu, string='Estimated Total Cost per Unit', type='float'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
