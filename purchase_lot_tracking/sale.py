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

class sale(orm.Model):

    _inherit = 'sale.order.line'

    def _minimum(self, cr, uid, ids, name, arg, context=None):
        res = {}
        account = self.pool.get('account.analytic.account')

        import ipdb; ipdb.set_trace()

        for id in ids:
            record = account.browse(cr, uid, id, context)
            minimum = 0.0
            once = False

            for value in record._data.values():
                if value.get('code'):
                    # Value points to a LOT
                    if value['quantity'] != 0:
                        tcu = value['total_cost_unit']
                        if not once:
                            minimum = tcu
                            once = True
                        elif tcu < minimum:
                            minimum = tcu

            res[id] = minimum

        return res

    def _average(self, cr, uid, ids, name, arg, context=None):
        res = {}
        account = self.pool.get('account.analytic.account')

        for id in ids:
            record = account.browse(cr, uid, id, context)
            average = 0.0
            total_count = 0

            for value in record._data.values():
                if value.get('code'):
                    # Value points to a LOT

                    quantity = value['quantity']
                    if quantity != 0:
                        average += quantity * value['total_cost_unit']
                        total_count += quantity

            try:
                res[id] = average / total_count
            except ZeroDivisionError:
                # Default to zero when nothing can be retrieved from account
                # lots
                res[id] = 0

        return res

    def _maximum(self, cr, uid, ids, name, arg, context=None):
        res = {}
        account = self.pool.get('account.analytic.account')

        for id in ids:
            record = account.browse(cr, uid, id, context)
            maximum = 0.0
            once = False

            for value in record._data.values():
                if value.get('code'):
                    # Value points to a LOT
                    if value['quantity'] != 0:
                        tcu = value['total_cost_unit']
                        if not once:
                            maximum = tcu
                            once = True
                        elif tcu > maximum:
                            maximum = tcu

            res[id] = maximum

        return res

    _columns = {
        'minimum': fields.function(_minimum, string='Min.', type='float'),
        'average': fields.function(_average, string='Avg.', type='float'),
        'maximum': fields.function(_maximum, string='Max.', type='float')
    }
