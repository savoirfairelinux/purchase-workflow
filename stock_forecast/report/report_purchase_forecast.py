from openerp import tools
from openerp.osv import osv, fields

class report_purchase_forecast(osv.osv):
    _name = "report.purchase.forecast"
    _description = "Purchase forecast"
    _auto = False
    _columns = {
        'test': fields.date('Date', readonly=True)
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_purchase_forecast')
        cr.execute("""
        CREATE OR REPLACE view report_purchase_forecast AS (
            SELECT
                date_trunc('day', current_date) as date
        );
        """)
        
report_purchase_forecast()
