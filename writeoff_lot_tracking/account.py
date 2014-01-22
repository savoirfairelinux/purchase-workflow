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

class account_voucher(orm.Model):

    _inherit = "account.voucher"

    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        '''
        Set a dict to be use to create the writeoff move line.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''

        currency_obj = self.pool.get('res.currency')
        move_line = {}

        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id

        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
            diff = line_total
            account_id = False
            write_off_name = ''
            if voucher.payment_option == 'with_writeoff':
                account_id = voucher.writeoff_acc_id.id
                write_off_name = voucher.comment
            elif voucher.type in ('sale', 'receipt'):
                account_id = voucher.partner_id.property_account_receivable.id
            else:
                account_id = voucher.partner_id.property_account_payable.id
            sign = voucher.type == 'payment' and -1 or 1

            # Create multiple move lines, one for each analytic account

            voucher_total = sum([l.amount for l in voucher.line_ids
                                 if l.reconcile])

            invoice_obj = self.pool.get('account.invoice')

            move_lines = []

            for voucher_line in voucher.line_ids:

                if voucher_line.reconcile:

                    invoice_ids = invoice_obj.search(cr, uid, [('number', '=', voucher_line.name)])
                    invoices = invoice_obj.browse(cr, uid, invoice_ids)
                    
                    invoice_ratio = voucher_line.amount / voucher_total
                    invoice_writeoff = diff * invoice_ratio

                    for invoice in invoices:
                        for invoice_line in invoice.invoice_line:
                            invoice_line_ratio = invoice_line.price_subtotal / invoice.amount_untaxed
                            invoice_line_writeoff = round(invoice_writeoff * invoice_line_ratio, 2)
                            
                            move_line = {
                                'name': write_off_name or name,
                                'account_id': account_id,
                                'move_id': move_id,
                                'partner_id': voucher.partner_id.id,
                                'date': voucher.date,
                                'credit': invoice_line_writeoff > 0 and invoice_line_writeoff or 0.0,
                                'debit': invoice_line_writeoff < 0 and -invoice_line_writeoff or 0.0,
                                'amount_currency': company_currency <> current_currency and (sign * -1 * voucher.writeoff_amount) or 0.0,
                                'currency_id': company_currency <> current_currency and current_currency or False,
                                'analytic_account_id': invoice_line.account_analytic_id.id or False,
                            }

                            move_lines.append(move_line)

                   
            writeoff_debit = sum([l['debit'] for l in move_lines])
            writeoff_credit = sum([l['credit'] for l in move_lines])

            if writeoff_debit > 0 and writeoff_debit != -diff:
                diff_writeoff = round(-diff - writeoff_debit, 2)
                move_lines[0]['debit'] = move_lines[0]['debit'] + diff_writeoff

            if writeoff_credit > 0 and writeoff_credit != diff:
                pass
                
            
            


        return move_lines



    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''

        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)
            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            line_total = move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)

            if ml_writeoff:
                for move_line in ml_writeoff:
                    move_line_pool.create(cr, uid, move_line, context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True
