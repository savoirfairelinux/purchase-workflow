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
import logging

class sale(orm.Model):

    _inherit = 'sale.order.line'
    _logger = logging.Logger(__name__)

    def _minimum(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for order_line in self.browse(cr, uid, ids, context):
            account = order_line.product_id.account_id
            minimum = 0.0

            if account:
                values = [lot.estimated_tcu for lot in account.child_ids
                          if lot.total_in_qty != 0]
            
                if values:
                    minimum = min(values)

            res[order_line.id] = minimum

        return res

    def _average(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for order_line in self.browse(cr, uid, ids, context):
            account = order_line.product_id.account_id
            average = 0.0
            
            total_count = 0

            if account:
                for lot in account.child_ids:
                    quantity = lot.total_in_qty
                    tcu = lot.estimated_tcu

                    if quantity != 0:
                        average += quantity * tcu
                        total_count += quantity
        
            if total_count == 0:
                res[order_line.id] = 0
            else:
                res[order_line.id] = average / total_count

        return res

    def _maximum(self, cr, uid, ids, name, arg, context=None):
        res = {}

        for order_line in self.browse(cr, uid, ids, context):
            account = order_line.product_id.account_id
            maximum = 0.0

            if account:
                values = [lot.estimated_tcu for lot in account.child_ids
                          if lot.total_in_qty != 0]

                if values:
                    maximum = max(values)

            res[order_line.id] = maximum

        return res

    _columns = {
        'minimum': fields.function(_minimum, string='Min.', type='float'),
        'average': fields.function(_average, string='Avg.', type='float'),
        'maximum': fields.function(_maximum, string='Max.', type='float')
    }
