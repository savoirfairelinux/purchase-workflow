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

class product_category(orm.Model):
    """
    Adds an analytical account to a purchase category
    """

    _inherit = 'product.category'

    _columns = {
        'account_id': fields.many2one('account.analytic.account', 'Analytical Account', required=False)
    }

class product_product(orm.Model):
    """
    Adds an analytical account to a purchase category
    """

    _inherit = 'product.product'

    _columns = {
        'account_id': fields.many2one('account.analytic.account', 'Analytical Account', required=False)
    }
