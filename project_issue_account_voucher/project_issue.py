# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2016 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)

class project_issue(models.Model):
    _inherit = 'project.issue'

    voucher_type = fields.Selection(selection_add=[('voucher_in','Supplier Voucher'),('voucher_out','Customer Voucher')], string='Voucher Type')

    @api.multi
    def voucher_in(self,):
        vouchers = []
        for issue in self:
            record = self.env['account.voucher'].with_context({'default_type': 'purchase', 'type': 'purchase'}).default_get(['journal_id','date','period_id'])
            record.update({
                'type': 'purchase',
                'account_id': issue.partner_id.property_account_receivable.id,
                'name': issue.description,
                'reference': issue.name,
            })
            voucher = self.env['account.voucher'].create(record)
            issue._finnish(voucher,_('Supplier voucher created'))
            vouchers.append(voucher)
        return self._get_views(voucher,'account_voucher.action_voucher_list', form='account_voucher.view_purchase_receipt_form')

    @api.multi
    def voucher_out(self,):
        vouchers = []
        for issue in self:
            record = self.env['account.voucher'].with_context({'default_type': 'sale', 'type': 'sale'}).default_get(['journal_id','date','period_id'])
            record.update({
                'type': 'sale',
                'account_id': issue.partner_id.property_account_payable.id,
                'name': issue.description,
                'reference': issue.name,
            })
            voucher = self.env['account.voucher'].create(record)
            issue._finnish(voucher,_('Customer voucher created'))
            vouchers.append(voucher)
        return self._get_views(voucher,'account_voucher.action_sale_receipt', form='account_voucher.view_sale_receipt_form')

class account_voucher(models.Model):
    _inherit = 'account.voucher'

    image = fields.Binary(compute='_image')
    @api.one
    @api.depends('partner_id')
    def _image(self):
        image = self.env['ir.attachment'].search([('res_model','=',self._name),('res_id','=',self.id)])
        if image and image[0].mimetype == 'application/pdf':
            self.image = image[0].image
        elif image and image[0].mimetype in ['image/jpeg','image/png','image/gif']:
            self.image = image[0].datas
        else:
            self.image = None
