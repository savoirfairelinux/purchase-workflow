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
from openerp.tools.translate import _


class stock_production_lot(orm.Model):

    _inherit = 'stock.production.lot'

    _columns = {
        'account_analytic_id': fields.many2one(
            'account.analytic.account',
            'Analytic Account',
            required=False
        )
    }


class stock_invoice_onshipping(orm.TransientModel):

    _inherit = 'stock.invoice.onshipping'

    def retrieve_move_lines(self, cr, uid, ids, context=None):
        """Retrieves all different move lines from the stock picking
        """
        move_lines = []
        for pick in self.pool.get('stock.picking').browse(
                cr, uid, context['active_ids'], context=context):
            move_lines += pick.move_lines

        return move_lines

    def _retrieve_invoice_lines(self, cr, uid, ids, context=None):
        """Retrieves invoice lines of a newly created invoice

           expects invoice_id to be passed in context
        """
        invoice = self.pool.get('account.invoice').browse(
            cr, uid, context['invoice_id'])
        return invoice.invoice_line

    def _find_matching_move_lines(self, invoice_line, move_lines):
        """Finds the matching invoice lines in the move lines list

           It is considered matching if they have the same product quantity,
           the same product id and the same production lot.

           :return: list of matching moving lines
        """
        cr = invoice_line._cr
        uid = invoice_line._uid
        context = invoice_line._context
        inv_line_pool = self.pool['account.invoice.line']
        matching_move_lines = [
            line for line in move_lines if
            line.product_qty == invoice_line.quantity and
            line.product_id.id == invoice_line.product_id.id
        ]

        duplicates = []
        if len(matching_move_lines) == 1:
            return [matching_move_lines[0]]
        elif len(matching_move_lines) > 1:
            for l in matching_move_lines:
                query = [
                    ('id', '!=', invoice_line.id),
                    ('invoice_id', '=', invoice_line.invoice_id.id),
                    ('product_id', '=', invoice_line.product_id.id),
                    ('quantity', '=', invoice_line.quantity),
                    ('account_analytic_id', '=',
                     l.prodlot_id.account_analytic_id.id)
                ]
                if not inv_line_pool.search(cr, uid, query, context=context):
                    return [l]
                else:
                    duplicates.append(l)

        return duplicates

    def merge_duplicate_invoice_lines(
            self, cr, uid, duplicate_ids, context=None):
        """Merge duplicate invoice lines: same product id, quantity
        and account analytic.

        Search for the main invoice line (the one which is duplicated).
        Modify its quantity (sum of all the same invoice lines) and
        delete duplicates.

        Sum quantities by multiplying since quantities are the same.

        :param list invoice_line_ids: duplicate invoice lines
        """
        invoice_line_pool = self.pool["account.invoice.line"]

        first_duplicate = invoice_line_pool.browse(cr, uid,
                                                   duplicate_ids[0],
                                                   context=context)
        invoice_id = first_duplicate.invoice_id.id
        product_id = first_duplicate.product_id.id
        quantity = first_duplicate.quantity
        account_analytic_id = first_duplicate.account_analytic_id.id

        query = [
            ('id', 'not in', duplicate_ids),
            ('invoice_id', '=', invoice_id),
            ('product_id', '=', product_id),
            ('quantity', '=', quantity),
            ('account_analytic_id', '=', account_analytic_id)
        ]

        main_obj_id = invoice_line_pool.search(cr, uid, query,
                                               context=context)[0]
        main_obj = invoice_line_pool.browse(cr, uid, main_obj_id,
                                            context=context)

        new_quantity = (len(duplicate_ids) + 1) * quantity
        main_obj.write({"quantity": new_quantity})

        invoice_line_pool.unlink(cr, uid, duplicate_ids, context=context)

    def create_invoice(self, cr, uid, ids, context=None):
        """
        Creates an invoice when the delivery lots are confirmed

        Iterates through all the lines of the invoice to specify
        the proper analytic_account
        """
        prod_lot_pool = self.pool.get('stock.production.lot')
        # creates the invoice properly
        res = super(stock_invoice_onshipping, self)\
            .create_invoice(cr, uid, ids, context=context)

        context['invoice_id'] = res.values()[0]

        # retrieve move lines of stock pickings
        move_lines = self.retrieve_move_lines(cr, uid, ids, context=context)

        # retrieve invoice lines of newly create invoice
        invoice_lines = self._retrieve_invoice_lines(cr, uid, ids,
                                                     context=context)

        # first iteration, check if matching
        lst_match = []
        to_merge = {}
        for invoice_line in invoice_lines:
            # don't add service to analytic account
            if invoice_line.product_id.type == u'service':
                continue
            matching_move_lines = self._find_matching_move_lines(invoice_line,
                                                                 move_lines)
            name = invoice_line.name
            if len(matching_move_lines) == 0:
                msg = _("The item %s is not in stock picking." % name)
                raise orm.except_orm(_("Missed line!"), msg)
            elif len(matching_move_lines) == 1:
                matching_move_line = matching_move_lines[0]
            else:
                if tuple(matching_move_lines) not in to_merge:
                    to_merge[tuple(matching_move_lines)] = []
                to_merge[tuple(matching_move_lines)].append(invoice_line.id)
                matching_move_line = matching_move_lines[0]

            # search account analytic
            prod_lot_id = matching_move_line.prodlot_id
            if not prod_lot_id:
                msg = _("The item '%s' missed 'prodlot_id' on associated move \
                item, origin %s." % (name, matching_move_line.origin))
                raise orm.except_orm(_("Missed Serial Number!"), msg)

            invoice_line.write(
                {'account_analytic_id': prod_lot_id.account_analytic_id.id})

        # merge duplicate invoice lines
        for duplicate_move_lines in to_merge:
            duplicate_invoice_lines = to_merge[duplicate_move_lines]
            self.merge_duplicate_invoice_lines(cr, uid,
                                               duplicate_invoice_lines,
                                               context=context)

        return res


class stock_picking_out(orm.Model):

    _inherit = 'stock.picking.out'

    def action_process(self, cr, uid, ids, context={}):
        '''Check if tracked products have their lot number specified'''

        picking = self.browse(cr, uid, ids, context=context)[0]

        for line in picking.move_lines:
            if line.product_id.track_production and not line.prodlot_id.id:
                message = ' '.join([
                    _('Please specify a lot number for all products of type:'),
                    line.product_id.name_template
                ])
                raise orm.except_orm(_('Missing lot number'), message)

        return super(stock_picking_out, self).action_process(
            cr, uid, ids, context)
