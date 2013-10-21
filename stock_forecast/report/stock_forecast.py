import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from openerp import tools, SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT 
from mako.template import Template

REPORT_TEMPLATE = u"""
<form string="Model" version="7.0">
  <table>
    <tr>
      <td style="text-align: center; vertical-align: middle; "></td>
      % for product in products:
      <td colspan="3" style="font-weight: bold; border-bottom: 1px black solid; font-size: 12pt; padding: 5px;">${product.name}</td>
      % endfor
    </tr>
    <tr>
      <td></td>
      % for product in products:
      <td style="font-weight: bold; border-left: 1px black solid; border-bottom: 1px black solid; padding: 2px;">Livrer</td>
      <td style="font-weight: bold; border-left: 1px black solid; border-right: 1px black solid; border-bottom: 1px black solid; padding: 2px;">Prevu</td>
      <td style="font-weight: bold; border-right: 1px black solid; border-left: 1px black solid; border-bottom: 1px black solid; text-align: center; vertical-align: middle; padding: 2px; ">Recevoir</td>
      % endfor
    </tr>
    % for day in days:
    <tr>
      <td style="font-size: 12pt; padding: 5px;">
        ${day['date']}
      </td>
      % for product in products:
      <td style="font-size: 12pt; color: ${day[product.id]['color']}; border-left: 1px black solid; border-bottom: 1px black solid; text-align: center; vertical-align: middle; ">
          ${day[product.id]['outgoing']}
      </td>
      <td style="font-size: 12pt; color: ${day[product.id]['color']}; border-bottom: 1px black solid; text-align: center; vertical-align: middle; ">
          ${day[product.id]['forecasted']}
      </td>
      <td style="font-size: 12pt; color: ${day[product.id]['color']}; border-right: 1px black solid; border-bottom: 1px black solid; text-align: center; vertical-align: middle; ">
          ${day[product.id]['incoming']}
      </td>
      % endfor
    </tr>

    % for order in day['orders']:
    <tr>
      <td style="text-align: right; padding: 5px;">
        ${order['label']}
      </td>
      % for product in products:
      <td style="border-bottom: 1px black solid; border-left: 1px black solid; text-align: center; vertical-align: middle; ">
        ${order[product.id]}
      </td>
      <td style="border-bottom: 1px black solid; vertical-align: middle; "></td>
      <td style="border-right: 1px black solid; border-bottom: 1px black solid; text-align: center; vertical-align: middle; "></td>
      % endfor
    </tr>
    % endfor

    % endfor
  </table>
</form>
"""

class stock_forecast_config(osv.osv_memory):
    _name = "stock.forecast.config"
    _description = "Stock Forecast"

    _columns = {
        'product_category': fields.many2one('product.category', 'Product Category', required=False)
    }

    def analytic_account_chart_open_window(self, cr, uid, ids, context=None):                                          
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result_context = {}
        if context is None:
            context = {}
        result = mod_obj.get_object_reference(cr, uid, 'stock_forecast', 'action_stock_forecast_form2')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        data = self.read(cr, uid, ids, [])[0]
        result_context.update({'product_category': data['product_category'][0]})
        result['context'] = result_context
        return result


stock_forecast_config()

class stock_forecast(osv.osv):
    _name = "stock.forecast"
    _description = "Stock forecast"
    _auto = False
    _columns = {
        'product_category': fields.many2one('product.category', 'Product Category', required=False)
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_forecast')
        cr.execute("""
        CREATE OR REPLACE view stock_forecast AS (
            SELECT
                1 as id,
                to_char(current_date, 'YYYY') as test
        );
        """)

    def get_timestamp(self, cr, uid, user_date, context=None):
        if context and context.get('tz'):
            tz_name = context['tz']
        else:
            tz_name = self.pool.get('res.users').read(cr, SUPERUSER_ID, uid, ['tz'])['tz']
        if tz_name:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            user_datetime = user_date + relativedelta(hours=12.0)
            local_timestamp = context_tz.localize(user_datetime, is_dst=False)
            user_datetime = local_timestamp.astimezone(utc)
            return user_datetime.strftime('%Y-%m-%d')
        return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def get_soumissions_ids(self, cr, uid, context=None):

        date_string = context['datetime'].strftime('%Y-%m-%d')
        date_string = self.get_timestamp(cr, uid, context['datetime'], context)
        product_ids = tuple(context['product_ids'])


        stock_moves = """SELECT id
                         FROM stock_move
                         WHERE sale_line_id IS NOT NULL
                         AND date_expected = '%s'::timestamp without time zone
                         AND product_id IN %s"""

        stock_moves = stock_moves % (date_string, product_ids)

        cr.execute(stock_moves)
        stock_moves_ids = list(sum(cr.fetchall(), ()))

        sale_order_lines = """SELECT id FROM sale_order_line
                                 WHERE id in (
                                     SELECT sale_line_id FROM stock_move
                                     WHERE id IN (
                                         %s
                                     )
                                 )
                           """

        sale_order_lines = sale_order_lines % stock_moves
        cr.execute(sale_order_lines);
        sale_order_line_ids = cr.fetchall()

        sale_orders = """SELECT id FROM sale_order
                         WHERE id in (
                             SELECT order_id FROM sale_order_line
                             WHERE id IN (
                                 %s
                             )
                         )
                         """
        
        cr.execute(sale_orders % sale_order_lines)
        sale_order_ids = list(sum(cr.fetchall(), ()))

        stock_moves = self.pool.get('stock.move').browse(cr, uid, stock_moves_ids)
        sale_orders = self.pool.get('sale.order').browse(cr, uid, sale_order_ids)

        quantities = {}

        for order in sale_orders:
            quantity = {}
            matching_ol_ids = [so.id for so in order.order_line]
            for order_line in order.order_line:
                matching_moves = filter(lambda x: x.product_id == order_line.product_id\
                                        and x.sale_line_id.id in matching_ol_ids,
                                        stock_moves)
                qty = quantity.get(order_line.product_id, 0)
                quantity[order_line.product_id.id] = sum([m.product_qty for m in matching_moves]) + qty

            quantities[order.id] = quantity
        return sale_orders, quantities


    def get_stock_outgoing(self, cr, uid, exp_day, context=None):

        date_string = self.get_timestamp(cr, uid, exp_day, context)
        product_id = context['product_id']

        # todo check sales as well
        query = """SELECT SUM(product_qty)
                          FROM stock_move
                          WHERE product_id = %s
                          AND sale_line_id IS NOT NULL
                          AND date_expected = '%s';"""

        cr.execute(query % (product_id, date_string))
        result = cr.fetchone()[0] or 0 
        return result

    def get_stock_incoming(self, cr, uid, exp_day, context=None):
      
        date_string = self.get_timestamp(cr, uid, exp_day, context)
        product_id = context['product_id']

        query = """SELECT SUM(sm.product_qty)
                          FROM stock_move sm,
                          stock_picking sp
                          WHERE sm.product_id = %s
                          AND sm.purchase_line_id IS NOT NULL
                          AND sm.picking_id = sp.id
                          AND sp.min_date = '%s';"""

        cr.execute(query % (product_id, date_string))
        result = cr.fetchone()[0] or 0 
        return result

    def get_stock_forecast(self, cr, uid, exp_day, context=None):

        product_id = context['product_id']
        product = self.pool.get('product.product').browse(cr, uid, [product_id], context=context)[0] 

        day_before = exp_day + timedelta(days=-1)
        date_string = self.get_timestamp(cr, uid, day_before)

        today_string = self.get_timestamp(cr, uid, datetime.now(), context)

        on_hand = product.qty_available
        # purchase
        incoming_ids = self.pool.get('stock.move').search(cr, uid, [('product_id', '=', product_id), '!',
                                                                    ('purchase_line_id', '=', None),
                                                                    ('date_expected', '>=', today_string),
                                                                    ('date_expected', '<', date_string) ])

        incoming = self.pool.get('stock.move').browse(cr, uid, incoming_ids)
      
        incoming_total = sum(i.product_qty for i in incoming)

                                                      
        outgoing_ids = self.pool.get('stock.move').search(cr, uid, [('product_id', '=', product_id), '!',
                                                                    ('sale_line_id', '=', None),
                                                                    ('date_expected', '>=', today_string),
                                                                    ('date_expected', '<', date_string) ])

        outgoing = self.pool.get('stock.move').browse(cr, uid, outgoing_ids)
        
        outgoing_total = sum(o.product_qty for o in outgoing)

        return on_hand + incoming_total - outgoing_total
        
    




        incoming_qty = self.get_stock_incoming(cr, uid, day_before, context=context)
        outgoing_qty = self.get_stock_outgoing(cr, uid, day_before, context=context)

        product = self.pool.get('product.product').browse(cr, uid, [product_id])[0]
        on_hand = product.qty_available
        print on_hand + incoming_qty - outgoing_qty
        return on_hand + incoming_qty - outgoing_qty


        
    def get_color(self, day_product):
      if day_product['outgoing'] > (day_product['forecasted'] + day_product['incoming']):
          return "#FF0000"

      if day_product['outgoing'] > day_product['forecasted']:
          return "#FF8000"

      return "#000000"
    

    def fields_view_get(self, cr, uid, view_id=None, view_type='tree', context=None, toolbar=False, submenu=False):
        result = super(stock_forecast, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

        forecast_context = {'product_id':5,
                            'datetime': datetime.now()}

        today = datetime.now()

        day_strings = []


        categ_id = context.get('product_category', 1)
        product_ids = self.pool.get('product.product').search(cr, uid, [('categ_id', '=', categ_id)])
        products = self.pool.get('product.product').browse(cr, uid, product_ids)

        products = [p for p in products ]
        

        days = []
        for day in range(14):

            product_strings = []
            exp_day = today + timedelta(days=day)

            day_has_moves = False

            day_values = {}
            day_values['date'] = exp_day.strftime('%Y-%m-%d')
            day_values['orders'] = []

            for product_id in product_ids:

                day_product = {}
                forecast_context = {'product_id': product_id,
                                    'datetime': exp_day }

                product = self.pool.get('product.product').browse(cr, uid, [product_id], context=None)[0]

                day_product['forecasted'] = self.get_stock_forecast(cr, uid, exp_day, context=forecast_context)
                day_product['outgoing'] = self.get_stock_outgoing(cr, uid, exp_day, context=forecast_context)
                day_product['incoming'] = self.get_stock_incoming(cr, uid, exp_day, context=forecast_context)
                day_product['color'] = self.get_color(day_product)
    

                if day_product['outgoing'] > 0:
                    day_has_moves = True

                day_values[product_id] = day_product

                
            if day_has_moves:
                order_lines, quantities = self.get_soumissions_ids(cr, uid, {'datetime': exp_day, 'product_ids': product_ids })
                for order in order_lines:

                    cells = []
                    order_values = {}
                    for product_id in product_ids:
                        qty = quantities[order.id].get(product_id, 0)
                        order_values[product_id] = qty

                    customer_name = order.partner_id.name
                    order_label = "%s (%s)" % (order.name, customer_name)
                    order_values['label'] = order_label
                    day_values['orders'].append(order_values)
            days.append(day_values)
        report = Template(REPORT_TEMPLATE).render_unicode(products=products, days=days)

        if view_type == 'form':
            result['arch'] = report
        return result


        
        
stock_forecast()
