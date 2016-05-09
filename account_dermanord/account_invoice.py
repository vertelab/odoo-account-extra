# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
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
import logging
_logger = logging.getLogger(__name__)

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    order_id = fields.Many2one(string='Sale order', comodel_name='sale.order')
    partner_shipping_id = fields.Many2one(comodel_name='res.partner', related='order_id.partner_shipping_id')
    picking_id = fields.Many2one(comodel_name='stock.picking', string='Picking')


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _make_invoice(self, order, lines):
        inv_id = super(sale_order, self)._make_invoice(order, lines)
        self.env['account.invoice'].browse(inv_id).write({'order_id' : order.id})
        return inv_id

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        vals['picking_id'] = picking.id
        invoice_id = super(stock_picking, self)._create_invoice_from_picking(picking, vals)
        return invoice_id
