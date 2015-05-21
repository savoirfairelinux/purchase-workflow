# -*- encoding: utf-8 -*-
# #############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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
###############################################################################
from openerp.tests import common
from datetime import date


class TestStock(common.TransactionCase):

    def setUp(self):
        """Setup the environment"""
        super(TestStock, self).setUp()

        self.user_model = self.registry("res.users")
        self.partner_model = self.registry("res.partner")
        self.picking_out_model = self.registry('stock.picking.out')
        self.product_model = self.registry("product.product")
        self.production_lot_model = self.registry('stock.production.lot')
        self.account_analytic_model = self.registry('account.analytic.account')
        self.invoice_model = self.registry('account.invoice')
        self.wizard_model = self.registry('stock.invoice.onshipping')

        self.context = self.user_model.context_get(self.cr, self.uid)

        cr, uid, context = self.cr, self.uid, self.context

        self.product_1_id = self.product_model.create(
            cr,
            uid,
            {'name': 'product_01',
             'type': 'consu',
             },
            context=context
        )

        self.product_2_id = self.product_model.create(
            cr,
            uid,
            {'name': 'product_02',
             'type': 'consu'},
            context=context
        )

        self.account_analytic_1_id = self.account_analytic_model.create(
            cr,
            uid,
            {'name': 'account_analytic_01',
             'type': 'normal'},
            context=context
        )

        self.account_analytic_2_id = self.account_analytic_model.create(
            cr,
            uid,
            {'name': 'account_analytic_02',
             'type': 'normal'},
            context=context
        )

        self.production_lot_1_id = self.production_lot_model.create(
            cr,
            uid,
            {'name': 'lot_01',
             'product_id': self.product_1_id,
             'date': date.today().strftime('%Y-%m-%d'),
             'account_analytic_id': self.account_analytic_1_id},
            context=context
        )

        self.production_lot_2_id = self.production_lot_model.create(
            cr,
            uid,
            {'name': 'lot_02',
             'product_id': self.product_2_id,
             'date': date.today().strftime('%Y-%m-%d'),
             'account_analytic_id': self.account_analytic_2_id},
            context=context
        )

        self.partner_id = self.partner_model.create(
            cr,
            uid,
            {'name': 'partner_01'},
            context=context
        )

        self.product_uom_id = self.registry('product.uom').search(
            cr, uid, [], context=context
        )[0]

        self.location_id = self.registry('stock.location').search(
            cr, uid, [('usage', '=', 'supplier')], context=context
        )[0]

        self.picking_id = self.picking_out_model.create(
            cr,
            uid,
            {'name': 'picking_01',
             'partner_id': self.partner_id,
             'invoice_state': '2binvoiced',
             'move_lines': [
                 (0, 0, {
                     'name': 'stock_move_01',
                     'product_id': self.product_1_id,
                     'product_qty': 10.0,
                     'product_uom': self.product_uom_id,
                     'date': date.today().strftime('%Y-%m-%d'),
                     'date_expected': date.today().strftime('%Y-%m-%d'),
                     'location_id': self.location_id,
                     'location_dest_id': self.location_id,
                     'prodlot_id': self.production_lot_1_id
                 }),
                 (0, 0, {
                     'name': 'stock_move_02',
                     'product_id': self.product_2_id,
                     'product_qty': 10.0,
                     'product_uom': self.product_uom_id,
                     'date': date.today().strftime('%Y-%m-%d'),
                     'date_expected': date.today().strftime('%Y-%m-%d'),
                     'location_id': self.location_id,
                     'location_dest_id': self.location_id,
                     'prodlot_id': self.production_lot_2_id
                 }),
                 (0, 0, {
                     'name': 'stock_move_03',
                     'product_id': self.product_1_id,
                     'product_qty': 10.0,
                     'product_uom': self.product_uom_id,
                     'date': date.today().strftime('%Y-%m-%d'),
                     'date_expected': date.today().strftime('%Y-%m-%d'),
                     'location_id': self.location_id,
                     'location_dest_id': self.location_id,
                     'prodlot_id': self.production_lot_1_id
                 })
                 ]},
            context=context
        )

        self.picking = self.picking_out_model.browse(
            cr, uid, self.picking_id
        )

    def test_create_invoice(self):
        """
        Test if invoice lines with same product id, quantity and account
        analytic are merged.
        Here, the stock picking contains 3 stock moves, the first and the last
        ones should be merged on the invoice.
        """
        cr, uid, context = self.cr, self.uid, self.context.copy()
        context['active_id'] = self.picking_id
        context['active_ids'] = [self.picking_id]
        context['active_model'] = self.picking_out_model._name
        self.wizard_id = self.wizard_model.create(
            cr, uid, {}, context=context)
        self.wizard_model.open_invoice(
            cr, uid, [self.wizard_id], context=context)
        self.invoice_id = self.invoice_model.search(
            cr, uid, [('origin', 'like', self.picking.name)], context=context
        )[0]
        self.invoice = self.invoice_model.browse(
            cr, uid, self.invoice_id
        )
        self.invoice_lines = self.invoice.invoice_line
        self.assertEqual(len(self.invoice_lines), 2,)
        merged_invoice_line = self.invoice_lines[0]
        self.assertEqual(merged_invoice_line.product_id.id,
                         self.product_1_id)
        self.assertEqual(merged_invoice_line.quantity, 20)
