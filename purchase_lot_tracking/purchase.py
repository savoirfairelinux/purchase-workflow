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
from openerp import netsvc

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
        Manages and tracks a lot number for this production line

        Generates a lot number, a stock.production.lot and an analytic
        account for this purchase order line.
        """
        for line_order in self.browse(cr, uid, ids):

            lot_number = self.pool.get('ir.sequence').get(cr, uid, 'ls.lot')
            product = line_order.product_id

            # Creates the analytic account
            account_id = self._analytic_account_from_product(cr, 
                                                uid,
                                                ids,
                                                {'product': product,
                                                 'lot_number': lot_number  })

            # Creates the stock.production.line
            serial_number_data = {'name': lot_number,
                                  'product_id': line_order.product_id.id,
                                  'account_analytic_id': account_id }

            serial_number_id = self.pool.get('stock.production.lot')\
                                            .create(cr, uid, serial_number_data)

            return serial_number_id, account_id
            


            

    def _analytic_account_from_product(self, cr, uid, ids, context):
        """
        Creates an analytic account for the lot number and places it
        as a children of the product's analytic account.

        Assumes two variables in the context
            - product: parent product id
            - lot_number: lot_number to create analytic account for
        """

        for line_order in self.browse(cr, uid, ids):
            
            product = context['product']
            parent_account = product.account_id

            account_values =  {
                'name': context['lot_number'],
                'complete_name': context['lot_number'],
                'code': context['lot_number'],
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

            analytic_account_id = self.pool.get('account.analytic.account')\
                                           .create(cr, uid, account_values)
            
            return analytic_account_id


    _columns = {
        'lot': fields.char('Lot Number', size=64, required=False, translate=True),
    }



class purchase_lot_tracking_purchase(orm.Model):
    """
    
    """
    _inherit = "purchase.order"

    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None): 
        
        if not picking_id:
            picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
        todo_moves = [] 
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for order_line in order_lines:
            if not order_line.product_id:
                continue
            if order_line.product_id.type in ('product', 'consu'):
                move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context))
                if order_line.move_dest_id:
                    order_line.move_dest_id.write({'location_id': order.location_id.id})
                todo_moves.append(move)
        stock_move.action_confirm(cr, uid, todo_moves)
        stock_move.force_assign(cr, uid, todo_moves)
        wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        res = [picking_id]


        pick_id = int(res[0])
        # landing costs Invoices from PO 
        #cost_obj = self.pool.get('landed.cost.position')
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        journal_obj = self.pool.get('account.journal')
        journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', order.company_id.id)], limit=1)

        # Create the analytic account

        stock_picking_id = self.pool.get('stock.picking.in').search(cr, uid, [('origin', 'like', order.name)])
        stock_picking = self.pool.get('stock.picking.in').browse(cr, uid, stock_picking_id)[0]
                            

        for po_line in order.order_line:
            import ipdb; ipdb.set_trace()
            lot_number, account_id = po_line.assign_lot_number()


            matching_line = [line for line in stock_picking.move_lines if\
                             line.product_qty == po_line.product_qty and \
                             line.product_id.id == po_line.product_id.id][0]

            matching_line.write({'prodlot_id': lot_number})            

            po_line.write({ 'account_analytic_id' : account_id })
            po_line.refresh()

        for order_cost in order.landed_cost_line_ids:
            vals_inv = { 
            'partner_id' : order_cost.partner_id.id
           #,'amount' : order_cost.amount
           #,'amount_currency' : order_cost.amount_currency
           ,'currency_id' : order_cost.currency_id.id or order.company_id.currency_id.id
           ,'account_id' : order_cost.partner_id.property_account_payable.id
           ,'type' : 'in_invoice'
           ,'origin' : order.name
           ,'fiscal_position':  order.partner_id.property_account_position and order.partner_id.property_account_positi
           ,'company_id': order.company_id.id
           ,'journal_id': len(journal_ids) and journal_ids[0] or False

                }   
            self._logger.debug('vals inv`%s`', vals_inv)
            inv_id = invoice_obj.create(cr, uid, vals_inv, context=None) 

            for po_line in order.order_line:
                
                # Create an invoice for the landed costs
                
                if order_cost.price_type == 'per_unit':
                    factor = po_line.product_qty / po_line.order_id.quantity_total
                
                elif order_cost.price_type == 'value':
                    factor = po_line.price_subtotal / po_line.order_id.amount_total
                amount = order_cost.amount * factor                

                vals_line = { 
                    'product_id' : order_cost.product_id.id
                    ,'name' : order_cost.product_id.name
                    #,'amount' : order_cost.amount
                    #,'amount_currency' : order_cost.amount_currency
                    #,'picking_id' : pick_id
                    ,'account_id' : self._get_product_account_expense_id(order_cost.product_id)
                    ,'partner_id' : order_cost.partner_id.id
                    ,'invoice_id' : inv_id
                    ,'account_analytic_id': po_line.account_analytic_id.id
                    ,'price_unit' : amount
                    ,'invoice_line_tax_id': [(6, 0, [x.id for x in order_cost.product_id.supplier_taxes_id])],

                }   
                self._logger.debug('vals line `%s`', vals_line)
                inv_line_id = invoice_line_obj.create(cr, uid, vals_line, context=None)  



        return res
