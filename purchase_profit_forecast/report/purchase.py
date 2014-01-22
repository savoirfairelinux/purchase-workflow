from openerp.osv import orm, fields
from datetime import datetime, timedelta

class purchase_profit(orm.Model):
    _name = "purchase.profit"
    _description = "Purchase Profit"
    _auto = False
    _log_access = True

    _columns = {
        'lot': fields.char('Lot', size=10),
        'purchase': fields.char('Purchase', size=10),
        'purchase landed costs': fields.char('Purchase Landed cost', size=10),
        'sales landed costs': fields.char('Sales Landed Costs', size=10),
        'refund': fields.char('Refund', size=10),
        'sale': fields.char('Sale', size=10),
        'balance': fields.char('Balance', size=10),
    }


class purchase_profit_config(orm.TransientModel):

    _name = "purchase.profit.config"
    _description = "Purchase Profit"

    _columns = {
        'start_date': fields.datetime('Start date'),
        'end_date': fields.datetime('End date')
    }

    _defaults = {
        'start_date': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'end_date': lambda *a: (
            datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    }


    def purchase_profit_open_window(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result_context = {}

        if context is None:
            context = {}

        result = mod_obj.get_object_reference(
            cr, uid, 'purchase_profit_forecast', 'action_purchase_profit')

        id = result and result[1] or False

        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['context'] = context
        return result

