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
