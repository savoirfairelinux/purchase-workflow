# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Savoir-faire Linux
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
##############################################################################

from openerp.osv import fields, orm


class split_in_production_lot(orm.TransientModel):
    """Get location_dest_id from wizard and add to stock.move"""
    _inherit = "stock.move.split"

    def default_get(self, cr, uid, fields, context=None):
        """Sets default destination location from stock.move"""
        res = super(split_in_production_lot, self).default_get(cr, uid, fields, context)
        if context.get('active_id'):
            move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
            if 'location_dest_id' in fields:
                res.update({'location_dest_id': move.location_dest_id.id})
        return res

    _columns = {
        'location_dest_id': fields.many2one('stock.location', 'Destination Location'),
    }

    def split(self, cr, uid, ids, move_ids, context=None):
        """Adds location to outputted moves"""
        new_moves = super(split_in_production_lot, self).split(cr, uid, ids, move_ids, context)
        move_obj = self.pool.get('stock.move')
        for data in self.browse(cr, uid, ids, context=context):
            if data.use_exist:
                lines = [l for l in data.line_exist_ids if l]
            else:
                lines = [l for l in data.line_ids if l]
            for current_move, line in zip(new_moves, lines):
                move_obj.write(cr, uid, [current_move], {'location_dest_id': line.location_dest_id.id})
        return new_moves


class stock_move_split_lines_exist(orm.TransientModel):
    """Adds location_dest_id to split view"""
    _inherit = "stock.move.split.lines"
    _columns = {
        'location_dest_id': fields.many2one('stock.location', 'Destination Location'),
    }

    def onchange_lot_id(self, cr, uid, ids, prodlot_id=False, product_qty=False, loc_id=False, product_id=False,
                        uom_id=False, context=None, location_dest_id=False, default_location_dest_id=False):
        """Adds default location_dest_id based on parent's"""
        res = super(stock_move_split_lines_exist, self).onchange_lot_id(cr, uid, ids, prodlot_id, product_qty, loc_id,
                                                                        product_id, uom_id, context=context)
        res['value'] = res.get('value') or {}
        res['value']['location_dest_id'] = location_dest_id or default_location_dest_id
        if not res['value']['location_dest_id']:
            del res['value']['location_dest_id']
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
