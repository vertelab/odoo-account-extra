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
        invoice_id = super(StockPicking, self)._create_invoice_from_picking(picking, vals)
        self.env['account.invoice'].browse(invoice_id).write({'incoterm': picking.sale_id.incoterm.id,
                       'weight': picking.weight,
                       'weight_net': picking.weight_net,
                       'weight_uom_id': picking.weight_uom_id.id,
                       'volume': picking.volume})
        return invoice_id

    @api.one
    def _package_ids(self):
        self.package_ids = [(6,0,set(self.pack_operation_ids.mapped('result_package_id.id')))]
    package_ids = fields.Many2many(comodel_name="stock.quant.package", compute='_package_ids')

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def _invoice_create_line(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('stock.move')
        invoices = {}
        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(cr, uid, moves, inv_type, context=context)
        product_price_unit = {}
        for move in moves:
            company = move.company_id
            origin = move.picking_id.name
            partner, user_id, currency_id = move_obj._get_master_data(cr, uid, move, company, context=context)

            key = (partner, currency_id, company.id, user_id)
            invoice_vals = self._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)

            if key not in invoices:
                # Get account and payment terms
                invoice_id = self._create_invoice_from_picking(cr, uid, move.picking_id, invoice_vals, context=context)
                invoices[key] = invoice_id
            else:
                invoice = invoice_obj.browse(cr, uid, invoices[key], context=context)
                merge_vals = {}
                if not invoice.origin or invoice_vals['origin'] not in invoice.origin.split(', '):
                    invoice_origin = filter(None, [invoice.origin, invoice_vals['origin']])
                    merge_vals['origin'] = ', '.join(invoice_origin)
                if invoice_vals.get('name', False) and (not invoice.name or (invoice_vals['name'] not in invoice.name.split(', ') if ', ' not in invoice_vals['name'] else invoice_vals['name'] not in invoice.name)):
                    invoice_name = filter(None, [invoice.name, invoice_vals['name']])
                    merge_vals['name'] = ', '.join(invoice_name)
                if merge_vals:
                    invoice.write(merge_vals)
            invoice_line_vals = move_obj._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=dict(context, fp_id=invoice_vals.get('fiscal_position', False)))
            invoice_line_vals['invoice_id'] = invoices[key]
            invoice_line_vals['origin'] = origin
            if not is_extra_move[move.id]:
                product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']] = invoice_line_vals['price_unit']
            if is_extra_move[move.id] and (invoice_line_vals['product_id'], invoice_line_vals['uos_id']) in product_price_unit:
                invoice_line_vals['price_unit'] = product_price_unit[invoice_line_vals['product_id'], invoice_line_vals['uos_id']]
            if is_extra_move[move.id]:
                desc = (inv_type in ('out_invoice', 'out_refund') and move.product_id.product_tmpl_id.description_sale) or \
                    (inv_type in ('in_invoice','in_refund') and move.product_id.product_tmpl_id.description_purchase)
                invoice_line_vals['name'] += ' ' + desc if desc else ''
                if extra_move_tax[move.picking_id, move.product_id]:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[move.picking_id, move.product_id]
                #the default product taxes
                elif (0, move.product_id) in extra_move_tax:
                    invoice_line_vals['invoice_line_tax_id'] = extra_move_tax[0, move.product_id]

            move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context=context)
            move_obj.write(cr, uid, move.id, {'invoice_state': 'invoiced'}, context=context)

        invoice_obj.button_compute(cr, uid, invoices.values(), context=context, set_total=(inv_type in ('in_invoice', 'in_refund')))
        return invoices.values()
