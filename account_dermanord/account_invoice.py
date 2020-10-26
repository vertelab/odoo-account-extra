# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models, fields, _
import openerp.addons.decimal_precision as dp
from openerp.osv import osv
from openerp.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)

    

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    order_id = fields.Many2one(string='Sale order', comodel_name='sale.order')
    partner_shipping_id = fields.Many2one(comodel_name='res.partner', related='order_id.partner_shipping_id')
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Picking')
    incoterm = fields.Many2one(comodel_name='stock.incoterms', string='Incoterm', help='International Commercial Terms are a series of predefined commercial terms used in international transactions.')
    weight = fields.Float(string='Gross Weight', digits_compute=dp.get_precision('Stock Weight'), help="The weight in Kg.")
    weight_net = fields.Float(string='Net Weight', digits_compute=dp.get_precision('Stock Weight'), help="The net weight in Kg.")
    weight_uom_id = fields.Many2one(string='Unit of Measure', comodel_name='product.uom')
    volume = fields.Float(string='Volume', digits_compute=dp.get_precision('Stock Weight'), help="The Volume in m3.")

    @api.multi
    def action_invoice_sent(self):
        if not self.partner_id.email:
            raise Warning("Kund saknar epostadress")
        return super(account_invoice, self).action_invoice_sent()
    
    @api.model
    @api.returns('self', lambda value: value.id)
    # ~ This is the controller for 0 amount auto confirm invoice
    def create(self, vals):
        invoice = super(account_invoice, self).create(vals)
        # This breaks tools like invoice merge. Probably best to define the situations
        # when we want to do this and make sure it only happens there.
        # ~ _logger.warn('\n\ncontext: %s\n' % self.env.context)
        # ~ if not self.env.context.get('override_0_invoice_confirm') and invoice.amount_total == 0:
            # ~ invoice.signal_workflow('invoice_open')
        return invoice
        
class sale_order(models.Model):
    _inherit = 'sale.order'
    
    @api.model
    def _make_invoice(self, order, lines):
        inv_id = super(sale_order, self)._make_invoice(order, lines)
        self.env['account.invoice'].browse(inv_id).write({'order_id' : order.id})
        return inv_id

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context)
        partner = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        res['value']['incoterm'] = partner.incoterm
        return res
    incoterm = fields.Many2one(comodel_name='stock.incoterms', string='Incoterm', help='International Commercial Terms are a series of predefined commercial terms used in international transactions.')

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        vals['picking_id'] = picking.id
        invoice_id = super(StockPicking, self.with_context(override_0_invoice_confirm=True))._create_invoice_from_picking(picking, vals)
        self.env['account.invoice'].browse(invoice_id).write({'incoterm': picking.sale_id.incoterm.id,
                       'weight': picking.weight,
                       'weight_net': picking.weight_net,
                       'weight_uom_id': picking.weight_uom_id.id,
                       'volume': picking.volume})
        return invoice_id

    # ~ @api.one
    # ~ def _package_ids(self):
        # ~ self.package_ids = [(6,0,set(self.pack_operation_ids.mapped('result_package_id.id')))]
        # ~ self.package_ids = [(4,shipping_weight)]
    # ~ package_ids = fields.Many2many(comodel_name="stock.quant.package", compute='_package_ids') #
    package_ids = fields.Many2many(comodel_name="stock.quant.package",store=True)
    
    shipping_weight = fields.Float(string='Shipping Weight')
    
class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"
    shipping_weight = fields.Float(string='Shipping Weight')
    
class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    use_cost_price = fields.Boolean(string='Use Cost Price', help = 'If you check this, cost price (standard_price) is used instead of Price (price_unit)')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def create_analytic_lines(self):
        acc_ana_line_obj = self.env['account.analytic.line']
        invoice = self.env.context.get('invoice')
        for obj_line in self:
            if obj_line.analytic_account_id.use_cost_price:
                if not obj_line.journal_id.analytic_journal_id:
                    raise osv.except_osv(_('No Analytic Journal!'),_("You have to define an analytic journal on the '%s' journal!") % (obj_line.journal_id.name, ))
                vals_line = self._prepare_analytic_line_products(obj_line, invoice)
                if vals_line:
                    line = obj_line.analytic_lines.filtered(lambda l: l.product_id == obj_line.product_id)
                    if line:
                        # Update existing analytic line
                        line.write(vals_line)
                    else:
                        # Create new analytic line
                        acc_ana_line_obj.create(vals_line)
            else:
                super(AccountMoveLine, obj_line).create_analytic_lines()
        return True
        
    @api.model
    def _prepare_analytic_line_products(self, obj_line, invoice):
        """
        Prepare the values given at the create() of account.analytic.line upon the validation of a journal item having
        an analytic account. This method is intended to be extended in other modules.

        :param obj_line: browse record of the account.move.line that triggered the analytic line creation
        """
        res = None
        if invoice and obj_line.product_id:
            res = self._prepare_analytic_line(obj_line)
            price_total = 0.0
            quantity_total = 0.0
            _logger.warn(invoice.invoice_line.filtered(lambda l: l.product_id == obj_line.product_id))
            for invoice_line in invoice.invoice_line.filtered(lambda l: l.product_id == obj_line.product_id):
                price_total += invoice_line.product_id.standard_price * invoice_line.quantity
                quantity_total += invoice_line.quantity
            res['amount'] = price_total
            res['unit_amount'] = quantity_total
        return res
