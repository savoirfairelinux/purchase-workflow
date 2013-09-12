# FIXME license

from openerp import netsvc
from openerp.osv import fields, orm

class sale_warn_under(orm.Model):

    _name = 'sale.order.warn'
    _description = 'Sale Order Warn'

    def _default_order_line_id(self, cr, uid, context=None):
        so_id = context['default_sale_order_id']
        sol_pool = self.pool.get('sale.order.line')

        # Get all Sale Order Lines for the current Sale Order
        sol_ids = sol_pool.search(cr, uid, [('order_id', '=', so_id)], context=context)

        # Filter for the relevant lines (unit price lower than minimum)
        sol_ids = [line.id for line in sol_pool.browse(cr, uid, sol_ids, context=context)
                if line.price_unit < line.minimum]

        return sol_ids

    def really_confirm(self, cr, uid, ids, context=None):
        so_id = context['default_sale_order_id']

        wf_service = netsvc.LocalService('workflow')
        self.pool.get('sale.order')._workflow_signal(cr, uid, [so_id], 'order_confirm', context=context)
        self.pool.get('sale.order').action_wait(cr, uid, [so_id], context=context)

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'sale_order_id': fields.many2one('sale.order'),
        'order_line_id': fields.one2many('sale.order.line', 'under_id', 'Justifications'),
    }

    _defaults = {
        'order_line_id': lambda self, cr, uid, context=None: self._default_order_line_id(cr, uid, context=context),
    }

