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

class purchase_order_line(orm.Model):

    _name = 'purchase.order.line'

    _columns = {
        'truck_line_id': fields.many2one('stock.truck.line', 'Truck line'),
    }


class stock_truck_line(orm.Model):

    _name = 'stock.truck.line'

    _columns = {
        'truck_id': fields.many2one('stock.truck', 'Truck'),
        'left_pallet': fields.one2many('purchase.order.line', 'truck_line_id', 'Pallet'),
        'right_pallet': fields.one2many('purchase.order.line', 'truck_line_id', 'Pallet'),
    }


class stock_truck(orm.Model):

    _name = 'stock.truck'

    _columns = {
        'front_temperature': fields.float('Front Temperature'),
        'back_temperature': fields.float('Back Temperature'),
        'truck_sn': fields.char('Truck S/N', size=64),
        'arrival': fields.date('Date of Arrival'),
        'pallet_ids': fields.one2many('stock.truck.line', 'truck_id', 'Pallets'),
    }
