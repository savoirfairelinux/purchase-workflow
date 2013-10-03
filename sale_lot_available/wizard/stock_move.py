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

from openerp.osv import fields, orm

class stock_production_lot(orm.Model):

    _inherit = 'stock.production.lot'

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        # Only override regular behaviour if on stock split wizard
        view_id = self.fields_view_get(cr, uid, context=context)['view_id']
        view = self.pool.get('ir.ui.view').browse(cr, uid, view_id, context=context)
        if view.model != 'stock.production.lot':
            return super(stock_production_lot, self).name_get(cr, uid, ids, context=context)

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = []

        for lot in self.browse(cr, uid, ids, context=context):
            res.append((lot.id, '%s / %.2f' % (lot.name, lot.stock_available)))

        return res
