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
    
    parcel_ids = fields.One2many(comodel_name='stock.quant.package', string='Parcels', compute='_get_parcel_ids')
    parcel_count = fields.Integer('Parcels', compute='_get_parcel_ids')
    
    @api.one
    def _get_parcel_ids(self):
        if self.picking_id:
            def get_top_package(package):
                if package.parent_id:
                    return get_top_package(package.parent_id)
                return package
            parcels = self.env['stock.quant.package'].browse()
            for package in self.picking_id.package_ids:
                parcels |= get_top_package(package)
            self.parcel_ids = parcels
            self.parcel_count = len(parcels)
    
    @api.multi
    def action_view_parcels(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('stock', 'action_package_view')
        res['domain'] = [('id', 'in', [p.id for p in self.parcel_ids])]
        res['views'] = [(self.env.ref('account_dermanord.view_quant_package_tree').id, 'tree')]
        return res

class stock_quant_package(models.Model):
    _inherit = 'stock.quant.package'
    
    shipping_ref = fields.Char('Shipping Reference')
    
    @api.multi
    def action_button_open_form(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('stock', 'action_package_view')
        res['res_id'] = self.id
        res['views'] = [(self.env.ref('stock.view_quant_package_form').id, 'form')]
        return res
        
