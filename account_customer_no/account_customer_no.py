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

    # ~ customer_no = fields.Char('Customer/Supplier Number', related="partner_id.customer_no", store=False)
    customer_no = fields.Char('Customer/Supplier Number', related="partner_id.customer_no", store=False, search="search_customer_no")
    
    @api.model
    def search_customer_no(self, op, value):
        partner_ids = [p['id'] for p in self.env['res.partner'].search_read([('customer_no',op,value)], ['id'])]
        return [('partner_id','in',partner_ids)]
    
class account_move(models.Model):
    _inherit = 'account.move'

    customer_no = fields.Char('Customer Number', related="partner_id.customer_no", store=False, search="search_customer_no")

    @api.model
    def search_customer_no(self, op, value):
        partner_ids = [p['id'] for p in self.env['res.partner'].search_read([('customer_no',op,value)], ['id'])]
        return [('partner_id','in',partner_ids)]
        
class account_move_line(models.Model):
    _inherit = 'account.move.line'

    customer_no = fields.Char('Customer Number', related="partner_id.customer_no", store=False, search="search_customer_no")

    @api.model
    def search_customer_no(self, op, value):
        partner_ids = [p['id'] for p in self.env['res.partner'].search_read([('customer_no',op,value)], ['id'])]
        return [('partner_id','in',partner_ids)]

class account_voucher(models.Model):
    _inherit = 'account.voucher'

    customer_no = fields.Char('Customer/Supplier Number', related="partner_id.customer_no", store=False, search="search_customer_no")

    @api.model
    def search_customer_no(self, op, value):
        partner_ids = [p['id'] for p in self.env['res.partner'].search_read([('customer_no',op,value)], ['id'])]
        return [('partner_id','in',partner_ids)]
