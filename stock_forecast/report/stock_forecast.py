from openerp import tools
from openerp.osv import osv, fields
from datetime import datetime, timedelta

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

    def get_stock_forecast(self, cr, uid, context=None):
        product_id = context['product_id']
        import pdb; pdb.set_trace()
        self.pool.get('stock_move').search(cr, uid, [('product_id', '=', product_id)])

    def fields_view_get(self, cr, uid, view_id=None, view_type='tree', context=None, toolbar=False, submenu=False):
        result = super(stock_forecast, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        from datetime import datetime

        forecast_context = {'product_id':5,
                            'datetime': datetime.now()}
        
        
        today = datetime.now()
        for product_id in range(5,6):
            for day in range(14):
                forecast_context = {'product_id': product_id,
                                    'datetime': today + timedelta(days=day) }
                forecast_for_day = self.get_stock_forecast(cr, uid, context=forecast_context)
                print "FORECAST: %s" % forecast_for_day
                                

        if view_type == 'form':
            result['arch'] = '''

        <form string="Model" version="7.0">
          <table>

          </table>
        </form>


            '''
        return result


        
        
stock_forecast()
