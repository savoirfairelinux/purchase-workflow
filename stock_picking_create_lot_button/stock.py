# -*- coding: utf-8 -*-
# #############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2013 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
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
from openerp.tools.translate import _
from purchase_lot_tracking import purchase


class stock_move_create_lot_button(orm.Model):
    _inherit = "stock.move"

    def btn_new_lot(self, cr, uid, ids, context=None):
        # suppose the button is call for only one id
        if not ids:
            return
        i_id = ids[0]
        actual_move = self.browse(cr, uid, i_id, context=context)
        # only generate for stock move in
        if actual_move.type != u'in':
            raise orm.except_orm('Error', 'Cannot create a lot in other situation of stock.move.in')
        if actual_move.prodlot_id:
            name = actual_move.prodlot_id.name
            msg = _("This move line has already an prodlot_id, ") + name
            raise orm.except_orm(_('Error'), msg)

        picking_id = actual_move.picking_id

        dct_po_line = {
            "order_id": picking_id.purchase_id,
            "product_id": actual_move.product_id,
        }

        po_line = self.Struct(**dct_po_line)
        lot_number, account_id = purchase.assign_lot_number(self.pool, cr, uid,
                                                            [po_line],
                                                            context=context)
        move_value = {
            'prodlot_id': lot_number,
            'partner_id': picking_id.partner_id.id,
            'price_unit': 0.0,
            'product_uos': 1,
            'state': 'assigned',
        }
        actual_move.write(move_value)
        # did we need to create a po line? No
        # po_line.write({'account_analytic_id': account_id})
        return True

    # transform dict to object
    class Struct:
        def __init__(self, **entries):
            self.__dict__.update(entries)
