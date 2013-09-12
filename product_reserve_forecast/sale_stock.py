# FIXME license

from openerp.osv import fields, orm
from openerp.tools import float_compare
from openerp.tools.translate import _

class sale_order_line(orm.Model):

    _inherit = 'sale.order.line'

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False, context=None):
        '''Slightly tweaked copy from sale_stock'''

        context = context or {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        warning = {}
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        if not product:
            res['value'].update({'product_packaging': False})
            return res

        #update of result obtained in super function
        product_obj = product_obj.browse(cr, uid, product, context=context)
        res['value']['delay'] = (product_obj.sale_delay or 0.0)
        res['value']['type'] = product_obj.procure_method

        #check if product is available, and if not: raise an error
        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if not uom2:
            uom2 = product_obj.uom_id

        # Calling product_packaging_change function after updating UoM
        res_packing = self.product_packaging_change(cr, uid, ids, pricelist, product, qty, uom, partner_id, packaging, context=context)
        res['value'].update(res_packing.get('value', {}))
        warning_msgs = res_packing.get('warning') and res_packing['warning']['message'] or ''

        # Original comparison did not substract reserved quantity
        avail = product_obj.virtual_available - product_obj.reserved
        compare_qty = float_compare(
                avail * uom2.factor,
                qty * product_obj.uom_id.factor,
                precision_rounding=product_obj.uom_id.rounding)

        if (product_obj.type=='product') and int(compare_qty) == -1 \
          and (product_obj.procure_method=='make_to_stock'):
            warn_msg = _('You plan to sell %.2f %s but you only have %.2f %s available !\nThe real stock is %.2f %s. (without reservations)') % \
                    (qty, uom2 and uom2.name or product_obj.uom_id.name,
                     max(0,product_obj.virtual_available), product_obj.uom_id.name,
                     max(0,product_obj.qty_available), product_obj.uom_id.name)
            warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"

        #update of warning messages
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        res.update({'warning': warning})
        return res
