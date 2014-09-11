# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
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


class stock_lot_valuation_wizard(orm.TransientModel):
    """Stock Lot Valuation Wizard"""

    _name = 'stock.lot.valuation.wizard'
    _description = _(__doc__)

    _columns = {
        'date_start': fields.datetime('Start date'),
        'date_end': fields.datetime('End date'),
    }

    _defaults = {
        'date_end': fields.datetime.now
    }

    def done(self, cr, uid, ids, context=None):
        context = context or {}

        wizard = self.browse(cr, uid, ids[0], context=context)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Lot Valuation'),
            'res_model': 'stock.lot.valuation',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'current',
            'context': {
                'date_start': wizard.date_start,
                'date_end': wizard.date_end,
                'search_default_by_product': 1,
                'search_default_groupby_prodlot_id': 1,
                'group_by': []
            },
            'domain': [
                ('date', '>=', wizard.date_start),
                ('date', '<=', wizard.date_end),
            ]
        }
