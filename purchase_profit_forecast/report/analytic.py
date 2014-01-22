from openerp.osv import orm, fields

class account_analytic_line(orm.Model):

    _inherit = 'account.analytic.line'

    def reference_po(self, cr, uid, ids, name, arg, context=None):

        res = {}
        for line in self.pool.get('account.analytic.line').browse(cr, uid, ids):

            res[line.id] = line.account_id.purchase_order.name

        return res

    _columns = {
        'reference_po': fields.function(reference_po,
                                        string='Reference PO',
                                        type='char',
                                        size=64,
                                        store=True),
    }
