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

class purchase_lot_tracking_product_category(orm.Model):
    """
    Adds an analytical account to a purchase category
    """

    _inherit = 'product.category'

    _columns = {
        'account_id': fields.many2one('account.analytic.account', 'Analytical Account', required=False)
    }

class purchase_lot_tracking_product_product(orm.Model):
    """
    Adds an analytical account to a purchase category
    """

    _inherit = 'product.product'

    _columns = {
        'account_id': fields.many2one('account.analytic.account', 'Analytical Account', required=False)
    }

class purchase_lot_tracking_purchase_purchase_order_line(orm.Model):
    """
    Adds an analytical account to a product
    """

    _inherit = 'purchase.order.line'

    def must_be_tracked(self, cr, uid, ids):
        """
        Determines if this purchase order line for this product must be tracked
        """
        return True

    def assign_lot_number(self, cr, uid, ids):
        """
        Generates a lot number for this purchase order line
        """
        for line_order in self.browse(cr, uid, ids):
            lot_number = self.pool.get('ir.sequence').get(cr, uid, 'ls.lot')
            line_order.write({'lot': lot_number})


    def create_analytic_account(self, cr, uid, ids):
        for line_order in self.browse(cr, uid, ids):
            product = line_order.product_id
            account = self._analytic_account_from_product(cr, 
                                                          uid,
                                                          ids,
                                                          {'product': product })

    _columns = {
        'lot': fields.char('Lot Number', size=64, required=False, translate=True),
    }


    def _analytic_account_from_product(self, cr, uid, ids, context):
        """
        Generates an analytic account from a product's analytic accoutn
        """
        product = context['product']
        parent_account = product.account_id
        lot_number = 'Lot #100'
        account_values =  {
            'name': parent_account.name + lot_number,
            'complete_name': parent_account.name + lot_number,
            'code': parent_account.code + lot_number,
            'type': 'normal',
            'parent_id': parent_account.id,
            'balance': 0.0,
            'debit': 0.0,
            'credit': 0.0,
            'quantity': 0.0,
            'date_start': parent_account.date_start,
            'date': parent_account.date,
            'state': parent_account.state,
            'currency_id': parent_account.currency_id.id,
            
        }
        return self.pool.get('account.analytic.account').create(cr, uid, account_values)

class purchase_lot_tracking_purchase(orm.Model):
    """
    """
    _inherit = "purchase.order"

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            for line in po.order_line:
                if line.must_be_tracked():
                    line.assign_lot_number()
                    line.create_analytic_account()
                    

            

