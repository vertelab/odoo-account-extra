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

class account_analytic_account(models.Model):
    _inherit = "account.analytic.account"


class project_issue(models.Model):
    _inherit = 'project.issue'


    @api.multi
    def create_invoice_customer(self,):
        for issue in self:
            invoice = self.env['account.invoice'].create({
            'origin': '%s (%d)' % (issue.name,issue.id),
            'type': 'out_invoice',
            'comment': issue.description,
            'company_id': issue.company_id.id,
            'user_id': issue.user_id.id,
            'account_id': issue.partner_id.property_account_receivable.id,
            'partner_id': issue.partner_id.id,
            })
            url = "<a href='/web?model=account.invoice&id=%d'>%s</a>" % (invoice.id,_('invoice'))
            issue.message_post(body=_('Customer Invoice created %s' % invoice.id) )
            for file in self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]):
                file.write({'res_model': 'account.invoice','res_id': invoice })
        return True

    @api.multi
    def create_invoice_supplier(self,):
        for issue in self:
            invoice = self.env['account.invoice'].create({
            'origin': issue.name,
            'type': 'in_invoice',
            'comment': issue.description,
            'company_id': issue.company_id.id,
            'user_id': issue.user_id.id,
            'account_id': issue.partner_id.property_account_payable.id,
            'partner_id': issue.partner_id.id,
            })
            for file in self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]):
                file.write({'res_model': 'account.invoice','res_id': invoice })
        return True

    @api.multi
    def create_move(self,):
        for issue in self:
            invoice = self.env['account.move'].create({
            'display_name': issue.name,
            'narration': issue.description,
            'company_id': issue.company_id.id,
            'to_check': true,
            })
            for file in self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]):
                file.write({'res_model': 'account.move','res_id': invoice })
        return True


    @api.multi
    def create_bank(self,):
        for issue in self:
            invoice = self.env['account.bank.statement'].create({
            'display_name': issue.name,
            'company_id': issue.company_id.id,
            })
            for file in self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]):
                file.write({'res_model': 'account.bank.statement','res_id': invoice })
        return True
