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

from openerp.osv import orm, fields, osv

class stock_production_lot(orm.Model):

    _inherit = 'stock.production.lot'

    _columns = {
        'account_analytic_id': fields.many2one('account.analytic.account', 'Analytic Account', required=False)
    }


class stock_invoice_onshipping(osv.osv_memory):

    _inherit = 'stock.invoice.onshipping'

    def retrieve_move_lines(self, cr, uid, ids, context=None):
        """Retrieves all different move lines from the stock picking
        """
        move_lines = []
        for pick in self.pool.get('stock.picking').browse(cr, uid,
                                                          context['active_ids'],
                                                          context=context):
            move_lines += pick.move_lines

        return move_lines

    def _retrieve_invoice_lines(self, cr, uid, ids, context=None):
        """Retrieves invoice lines of a newly created invoice

           expects invoice_id to be passed in context
        """
        invoice = self.pool.get('account.invoice')\
                           .browse(cr,uid, context['invoice_id'])
        return invoice.invoice_line

    def _find_matching_move_line(self, invoice_line, move_lines):
        """Finds the matching invoice line in the move lines list

           It is considered matching if they have the same product quantity
           and the same product id.
        """
        matching_move_lines = [line for line in move_lines if
                               line.product_qty == invoice_line.quantity and
                               line.product_id.id == invoice_line.product_id.id]

        return matching_move_lines[0]

    def create_invoice(self, cr, uid, ids, context=None):
        """
        Creates an invoice when the delivery lots are confirmed

        Iterates through all the lines of the invoice to specify
        the proper analytic_account
        """
        # creates the invoice properly
        res = super(stock_invoice_onshipping, self)\
            .create_invoice(cr, uid, ids, context=context)

        context['invoice_id'] = res.values()[0]
        
        # retrieve move lines of stock pickings
        move_lines = self.retrieve_move_lines(cr, uid, ids, context=context)

        # retrieve invoice lines of newly create invoice
        invoice_lines = self._retrieve_invoice_lines(cr, uid, ids,
                                                    context=context)

        for invoice_line in invoice_lines:
            matching_move_line = self._find_matching_move_line(invoice_line,
                                                               move_lines)

            
            prodlot_id = matching_move_line.prodlot_id

            matching_prodlot = self.pool.get('stock.production.lot')\
                                        .browse(cr, uid, [prodlot_id])[0]
            
            matching_account = matching_prodlot.id.account_analytic_id.id

            invoice_line.write({'account_analytic_id': matching_account})
        
        return res
