from openerp import tools
from openerp.osv import osv, fields

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
        
stock_forecast()
