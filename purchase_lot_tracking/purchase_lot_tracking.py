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
from openerp import netsvc
import openerp.addons.decimal_precision as dp

from datetime import datetime

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
            
            serial_number_data = {'name': lot_number,
                                  'product_id': line_order.product_id.id }

            serial_number_id = self.pool.get('stock.production.lot')\
                                              .create(cr, uid, serial_number_data)

            line_order.write({'lot': lot_number})
            
            return serial_number_id
            


    def create_analytic_account(self, cr, uid, ids):

        for line_order in self.browse(cr, uid, ids):
            product = line_order.product_id
            account_id = self._analytic_account_from_product(cr, 
                                                          uid,
                                                          ids,
                                                          {'product': product })

            
            return account_id


            

    def _analytic_account_from_product(self, cr, uid, ids, context):
        """
        Generates an analytic account from a product's analytic accoutn
        """

        for line_order in self.browse(cr, uid, ids):
            
            product = context['product']
            parent_account = product.account_id
            lot_number = line_order.lot
            account_values =  {
                'name': lot_number,
                'complete_name': lot_number,
                'code': lot_number,
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

            analytic_account_id = self.pool.get('account.analytic.account').create(cr, uid, account_values)
            
            return analytic_account_id

            #self._create_analytic_entry_for_po_line(line_order, analytic_account_id, cr, uid)
            #self._create_analytic_entry_for_po_landed_costs(line_order, analytic_account_id, cr, uid)


    def _create_analytic_entry_for_po_line(self, 
                                           po_line,
                                           analytic_account_id,
                                           cr,
                                           uid):
        
        account_line_values = {
            'name': po_line.name,
            'date': datetime.now(),
            'amount': po_line.price_subtotal,
            'account_id': analytic_account_id,
            # FIXME: add proper values
            'general_account_id': 113,
            'journal_id': 3,
        }

        self.pool.get('account.analytic.line').create(cr, uid, account_line_values)


    def _create_analytic_entry_for_po_landed_costs(self,
                                                   po_line,
                                                   analytic_account_id,
                                                   cr,
                                                   uid):
        
        for landed_cost_line_id in po_line.order_id.landed_cost_line_ids:
            if landed_cost_line_id.price_type == 'per_unit':
                factor = po_line.product_qty / po_line.order_id.quantity_total
                
            elif landed_cost_line_id.price_type == 'value':
                factor = po_line.price_subtotal / po_line.order_id.amount_total
            amount = landed_cost_line_id.amount * factor
            name = landed_cost_line_id.product_id.name
                

            account_line_values = {
                'name': name,
                'date': datetime.now(),
                'amount': amount,
                'account_id': analytic_account_id,
                # FIXME: add proper values
                'general_account_id': 113,
                'journal_id': 3,
            }

            self.pool.get('account.analytic.line').create(cr, uid, account_line_values)


    _columns = {
        'lot': fields.char('Lot Number', size=64, required=False, translate=True),
    }



class purchase_lot_tracking_purchase(orm.Model):
    """
    
    """
    _inherit = "purchase.order"

    #def wkf_confirm_order(self, cr, uid, ids, context=None):
    #    for po in self.browse(cr, uid, ids, context=context):
    #        for line in po.order_line:
    
    #            if line.must_be_tracked():
    #                line.assign_lot_number()
    #                line.create_analytic_account()
                    

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
            lot_number = po_line.assign_lot_number()
            account_id = po_line.create_analytic_account()

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

class stock_invoice_onshipping(osv.osv_memory):

    _inherit = 'stock.invoice.onshipping'

    def create_invoice(self, cr, uid, ids, context=None):
        res = super(stock_invoice_onshipping, self).create_invoice(cr, uid, ids, context=context)
        
        move_lines = []
        for pick in self.pool.get('stock.picking').browse(cr, uid, context['active_ids'], context=context):
            move_lines = move_lines + pick.move_lines

        invoice_id = res.values()[0]
        invoice = self.pool.get('account.invoice').browse(cr, uid, res.values()[0])

        for invoice_line in invoice.invoice_line:
            matching_move_line = [line for line in move_lines if
                                  line.product_qty == invoice_line.quantity and
                                  line.product_id.id == invoice_line.product_id.id][0]
            
            prodlot_id = matching_move_line.prodlot_id

            matching_prodlot = self.pool.get('stock.production.lot').browse(cr, uid, [prodlot_id])[0]
            
            matching_account = self.pool.get('account.analytic.account').search(cr, uid, [('name', 'like', matching_prodlot.id.name)])

            invoice_line.write({'account_analytic_id': matching_account[0]})
        
        return res

#class stock_partial_picking(orm.Model):

#    _inherit = 'stock.picking.in'

#    def action_process(self, cr, uid, ids, context=None):

#        if context is None:
#            context = {} 
#            """Open the partial picking wizard"""
#            context.update({
#                'active_model': self._name,
#                'active_ids': ids, 
#                'active_id': len(ids) and ids[0] or False
#            })   
#
#        for stock_picking in self.browse(cr, uid, ids):
#            import ipdb; ipdb.set_trace()            
#            ref_po_id = self.pool.get('purchase.order').search(cr, uid, [('name', 'like', stock_picking.origin)])
#            ref_po = self.pool.get('purchase.order').browse(cr, uid, ref_po_id)[0]
#
#            for stock_picking_line in stock_picking.move_lines:
#                
#                matching_line = [po_line for po_line in ref_po.order_line if\
#                                 po_line.product_qty == stock_picking_line.product_qty and \
#                                 po_line.product_id.id == stock_picking_line.product_id.id][0]
#
##                matching_lot = self.pool.get('stock.production.lot').search(cr, uid, [('name', 'like', matching_line.lot)])[0]
#
#                stock_picking_line.write({'prodlot_id': matching_lot})
#                stock_picking_line.refresh()



#        return {
#            'view_type': 'form',
#            'view_mode': 'form',
#            'res_model': 'stock.partial.picking',
#            'type': 'ir.actions.act_window',
#            'target': 'new',
#            'context': context,
#            'nodestroy': True,
#        }   
