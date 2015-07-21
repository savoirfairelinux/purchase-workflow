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
from openerp import tools


class stock_lot_valuation(orm.Model):
    """Stock Lot Valuation Report"""

    _name = 'stock.lot.valuation'
    _description = _(__doc__)
    _auto = False

    def _product_qty(self, cr, uid, ids, field, args, context=None):
        context = context or {}

        res = {}

        location_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context
        ).company_id.partner_id.property_stock_customer.id

        for line in self.browse(cr, uid, ids, context=context):
            if line.move_id.location_id.id == location_id:
                res[line.id] = line.move_id.product_qty
            elif line.move_id.location_dest_id.id == location_id:
                res[line.id] = line.move_id.product_qty * (-1)
            else:
                res[line.id] = 0.0

        return res

    _columns = {
        'name': fields.char('Name'),
        'move_id': fields.many2one('stock.move', 'Stock Move'),
        'product_id': fields.many2one('product.product', 'Product'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot #'),
        'product_qty': fields.float('Quantity on hand'),
        'location_id': fields.many2one('stock.location', 'Source Location'),
        'location_dest_id': fields.many2one('stock.location', 'Dest Location'),
        'valuation': fields.float('Valuation'),
        'date': fields.datetime('Move date'),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_lot_valuation')
        cr.execute("""
            CREATE OR REPLACE FUNCTION get_company_stock_location(integer) RETURNS integer AS $$
            DECLARE
                company_id ALIAS FOR $1;
                partner_rec RECORD;
                property_rec RECORD;
                res TEXT;
            BEGIN
                EXECUTE 'SELECT partner_id FROM res_company WHERE id = $1'
                   INTO partner_rec
                   USING company_id;

                res := 'res.partner,'||partner_rec.partner_id;

                SELECT a.value_reference INTO property_rec FROM ir_property a WHERE a.name = 'property_stock_customer' AND a.res_id = res;

                RETURN substring(property_rec.value_reference from position(',' in property_rec.value_reference)+1)::integer;
            END;
            $$ LANGUAGE plpgsql;


            CREATE OR REPLACE FUNCTION valuation_by_move(integer, integer) RETURNS numeric AS $$
            DECLARE
                move_id ALIAS FOR $1;
                account_id ALIAS FOR $2;
                valuation numeric;
                aaa_values RECORD;
                move_values RECORD;
            BEGIN
                EXECUTE 'SELECT
                            CASE
                              WHEN
                                location_id = get_company_stock_location(company_id) AND
                                location_dest_id != get_company_stock_location(company_id)
                              THEN product_qty * -1
                              WHEN
                                location_dest_id = get_company_stock_location(company_id) AND
                                location_id != get_company_stock_location(company_id)
                              THEN product_qty
                            END AS product_qty
                         FROM stock_move
                         WHERE id = $1'
                   INTO move_values
                   USING move_id;

                EXECUTE 'SELECT
                             a.id,
                             sum(
                                 CASE WHEN l.amount > 0
                                 THEN l.amount
                                 ELSE 0.0
                                 END
                             ) as debit,
                             sum(
                                 CASE WHEN l.amount < 0
                                 THEN -l.amount
                                 ELSE 0.0
                                 END
                             ) as credit,
                             COALESCE(SUM(l.amount),0) AS balance,
                             COALESCE(SUM(l.unit_amount),0) AS quantity,
                             total_in_qty,
                             total_cost_unit
                         FROM account_analytic_account a
                             LEFT JOIN account_analytic_line l ON (a.id = l.account_id)
                         WHERE a.id = $1
                         GROUP BY a.id'
                    INTO aaa_values
                    USING account_id;
                valuation := aaa_values.total_cost_unit * move_values.product_qty;
                RETURN valuation;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE VIEW stock_lot_valuation AS (
                SELECT
                   a.id AS id,
                   a.id AS move_id,
                   b.name_template AS name,
                   a.product_id AS product_id,
                   a.prodlot_id,
                   a.location_id,
                   a.location_dest_id,
                   12 AS stock_location_id,
                   CASE
                      WHEN
                        a.location_id = get_company_stock_location(a.company_id) AND
                        a.location_dest_id != get_company_stock_location(a.company_id)
                      THEN product_qty * -1
                      WHEN
                        a.location_dest_id = get_company_stock_location(a.company_id) AND
                        a.location_id != get_company_stock_location(a.company_id)
                      THEN product_qty
                   END AS product_qty,
                   a.date,
                   valuation_by_move(a.id, c.id) as valuation,
                   date_trunc('day',a.create_date) as create_date,
                   a.company_id
                FROM
                   stock_move a,
                   product_product b,
                   account_analytic_account c,
                   stock_production_lot d,
                   res_company f
                WHERE
                   a.product_id = b.id AND
                   a.state = 'done' AND
                   a.prodlot_id = d.id AND
                   d.name = c.code AND
                   f.id = a.company_id
            )""")
