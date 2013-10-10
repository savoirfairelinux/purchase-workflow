from openerp import tools
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from mako.template import Template


REPORT_TEMPLATE = """
<form string="Model" version="7.0">
  <table>
    <tr>
      <td></td>
      % for product in products:
      <td colspan="2">${product.name}</td>
      % endfor
    </tr>
    % for day in days:
    <tr>
      <td>
        ${day['date']}
      </td>
      % for product in products:
      <td>
        ${day[product.id]['outgoing']}
      </td>
      <td>
        ${day[product.id]['forecasted']}
      </td>
      % endfor
    </tr>
    
    % for order in day['orders']:
    <tr>
      <td>
        ${order['label']}
      </td>
      % for product in products:
      <td colspan="2">
        ${order[product.id]}
      </td>
      % endfor
    </tr>
    % endfor

    % endfor
  </table>
</form>
"""



class stock_forecast(osv.osv):
    _name = "stock.forecast"
    _description = "Stock forecast"
    _auto = False
    _columns = {
        'test': fields.char('Date', size=4, readonly=True)
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

    def get_soumissions_ids(self, cr, uid, context=None):

        date_string = context['date'].strftime('%Y-%m-%d')
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


    def get_stock_outgoing(self, cr, uid, context=None):

        date_string = context['datetime'].strftime('%Y-%m-%d')
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

    def get_stock_forecast(self, cr, uid, context=None):

        product_id = context['product_id']
        date_string = context['datetime'].strftime('%Y-%m-%d')
        today_string = datetime.now().strftime('%Y-%m-%d')

        product = self.pool.get('product.product').browse(cr, uid, [product_id])[0]
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


        
    
    

    def fields_view_get(self, cr, uid, view_id=None, view_type='tree', context=None, toolbar=False, submenu=False):
        result = super(stock_forecast, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        from datetime import datetime

        forecast_context = {'product_id':5,
                            'datetime': datetime.now()}
        
        
        today = datetime.now()

        day_strings = []


        product_ids = self.pool.get('product.product').search(cr, uid, [('categ_id', '=', 1)])
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

                day_product['forecasted'] = self.get_stock_forecast(cr, uid, context=forecast_context)
                day_product['outgoing'] = self.get_stock_outgoing(cr, uid, context=forecast_context)
                
                if day_product['outgoing'] > 0:
                    day_has_moves = True

                color = 'black'
                
                day_values[product_id] = day_product

            day_strings.append(day_template % {'date_string': exp_day.strftime('%Y-%m-%d'),
                                               'product_string': ''.join(product_strings) })
                
            if day_has_moves:
                order_lines, quantities = self.get_soumissions_ids(cr, uid, {'date': exp_day, 'product_ids': product_ids })
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
