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

from openerp.osv import orm


class stock_move(orm.Model):
    _inherit = "stock.move"

    def action_consume(self, cr, uid, ids, quantity, location_id=False, context=None):
        """ Consumed product with specific quatity from specific source location
        @param cr: the database cursor
        @param uid: the user id
        @param ids: ids of stock move object to be consumed
        @param quantity : specify consume quantity
        @param location_id : specify source location
        @param context: context arguments
        @return: Consumed lines
        """
        stock_move_obj = self.browse(cr, uid, ids, context=context)[0]
        if stock_move_obj and stock_move_obj.location_id and stock_move_obj.location_id.name == 'Production':
            self.autoassign_newlot(cr, uid, ids, stock_move_obj, context=context)
        return super(stock_move, self).action_consume(cr, uid, ids, quantity, location_id, context=context)

    def autoassign_newlot(self, cr, uid, ids, stock_move_obj, context=None):
        """
        Generate and assign a new stock_production_lot to consumable product.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param stock_move_obj: the browse object of the stock
        @param context: A standard dictionary
        @return:
        """
        # Pools
        stock_move_pool = self.pool.get('stock.move')
        # Get product account
        consumed_stock_move_id = stock_move_pool.search(cr, uid, [('move_dest_id', '=', stock_move_obj.id)])[0]
        consumed_stock_move = stock_move_pool.browse(cr, uid, consumed_stock_move_id, context=context)
        product_account = consumed_stock_move.prodlot_id.account_analytic_id
        # Generate next Lot name
        new_lot_name = self.pool.get('ir.sequence').next_by_code(cr, uid, 'ls.lot', context=context)
        # Create new analytic account
        vals = {
            'name': new_lot_name,
            'code': new_lot_name,
            'parent_id': stock_move_obj.product_id.id,
            'state': product_account.state,
            'type': product_account.type,
            'company_id': product_account.company_id and product_account.company_id.id,
            'manager_id': product_account.manager_id and product_account.manager_id.id,
            'template_id': product_account.template_id and product_account.template_id.id,
            'purchase_order': product_account.purchase_order and product_account.purchase_order.id,
        }
        new_analytic_account_id = self.pool.get('account.analytic.account').create(cr, uid, vals)
        # Create new lot id
        vals = {
            'name': new_lot_name,
            'account_analytic_id': new_analytic_account_id,
            'product_id': stock_move_obj.product_id and stock_move_obj.product_id.id,
        }
        new_lot_id = self.pool.get('stock.production.lot').create(cr, uid, vals, context=context)
        # Assign new lot number
        self.write(cr, uid, stock_move_obj.id, {'prodlot_id': new_lot_id})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
