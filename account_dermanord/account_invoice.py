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

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        vals['picking_id'] = picking.id
        invoice_id = super(stock_picking, self)._create_invoice_from_picking(picking, vals)
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
