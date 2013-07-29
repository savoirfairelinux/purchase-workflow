# -*- coding: utf-8 -*-                                                                                                                                                                                                                        
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
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

import time
from lxml import etree
from openerp.osv import fields, osv 
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class stock_partial_picking_line(osv.TransientModel):

    def _tracking(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for tracklot in self.browse(cursor, user, ids, context=context):
            tracking = False
            if (tracklot.move_id.picking_id.type == 'in' and tracklot.product_id.track_incoming == True) or \
                (tracklot.move_id.picking_id.type == 'out' and tracklot.product_id.track_outgoing == True):
                tracking = True
            res[tracklot.id] = tracking
        return res 

    _inherit  = "stock.partial.picking.line"

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):

        raise Exception()

        uom_id = False
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            uom_id = product.uom_id.id
        return {'value': {'product_uom': uom_id}}

