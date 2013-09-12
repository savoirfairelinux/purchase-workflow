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

from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools.translate import _

class sale_order_line(orm.Model):

    _inherit = 'sale.order.line'

    _columns = {
        'under_minimum_reason': fields.text('Reason'),
        'under_id': fields.many2one('sale.order.warn', 'Justifications'),
    }


class sale_order(orm.Model):

    _inherit = 'sale.order'

    def action_confirm_warn(self, cr, uid, ids, context=None):
        '''Either return a warning, or move along'''

        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        assert len(ids) == 1, 'This option should only be used for a single ID at a time.'

        so_lines = self.browse(cr, uid, ids, context=context)[0].order_line

        if any(line.price_unit < line.minimum for line in so_lines):
            # If there is at least one line where the unit price is lower than
            # the minimum price in stock, display the warning wizard requiring
            # a comment over that price

            active = self.browse(cr, uid, ids, context=context)[0].id

            return {
                'type': 'ir.actions.act_window',
                'name': _('Sale Under Minimum Warning'),
                'res_model': 'sale.order.warn',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'nodestroy': True,
                'context': {'default_sale_order_id': active},
            }

        # Recreate original behaviour from core action_button_confirm()

        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)
        self.action_wait(cr, uid, ids, context=context)

        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
        view_id = view_ref and view_ref[1] or False

        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

        return True
