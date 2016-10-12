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
import time
import logging
_logger = logging.getLogger(__name__)

class account_analytic_default(models.Model):
    _inherit = 'account.analytic.default'

    bom_id = fields.Many2one(comodel_name='mrp.bom', string='BOM')

    @api.model
    def bom_account_create(self,line):        
        account = self.env['account.analytic.default'].account_get(line.product_id.id if line.product_id else None, line.invoice_id.partner_id.id, line.invoice_id.user_id.id, time.strftime('%Y-%m-%d'))
        _logger.warn(account)
        if account and account.bom_id:
            move_line = line.invoice_id.move_id.line_id.filtered(lambda l: len(l.analytic_lines) > 0)
            if move_line:
                move_line = move_line[0]
            for b in account.bom_id.bom_line_ids:
                account_standard = self.env['account.analytic.default'].account_get(b.product_id.id if b.product_id else None, line.invoice_id.partner_id.id, line.invoice_id.user_id.id, time.strftime('%Y-%m-%d'))
                _logger.warn('account_standard',account_standard)
                if account_standard:
                    if account_standard.analytics_id and account_standard.analytics_id.account_ids:
                        for account in account_standard.analytics_id.account_ids:
                            currency = line.invoice_id.currency_id.with_context(date=line.invoice_id.date_invoice)
                            self.env['account.analytic.line'].create({
                                'move_id': move_line.id if move_line else None,
                                'name': line.name,
                                'date': line.invoice_id.date_invoice,
                                'account_id': account.analytic_account_id.id,
                                'unit_amount': line.quantity * b.product_uos_qty,  
                                'amount': currency.compute(line.price_subtotal, line.invoice_id.company_id.currency_id) * 1 if line.invoice_id.type in ('out_invoice', 'in_refund') else -1 * account.rate / 100.0,
                                'product_id': b.product_id.id,
                                'product_uom_id': b.product_uos.id,
                                'general_account_id': line.account_id.id,
                                'journal_id': line.invoice_id.journal_id.analytic_journal_id.id,
                                'ref': line.invoice_id.reference if line.invoice_id.type in ('in_invoice', 'in_refund') else line.invoice_id.number,
                            })
                    else:
                        currency = line.invoice_id.currency_id.with_context(date=line.invoice_id.date_invoice)
                        self.env['account.analytic.line'].create({
                            'move_id': move_line.id if move_line else None,
                            'name': line.name,
                            'date': line.invoice_id.date_invoice,
                            'account_id': line.account_analytic_id.id,
                            'unit_amount': line.quantity * b.product_uos_qty,  
                            'amount': currency.compute(line.price_subtotal, line.invoice_id.company_id.currency_id) * 1 if line.invoice_id.type in ('out_invoice', 'in_refund') else -1,
                            'product_id': b.product_id.id,
                            'product_uom_id': b.product_uos.id,
                            'general_account_id': line.account_id.id,
                            'journal_id': line.invoice_id.journal_id.analytic_journal_id.id,
                            'ref': line.invoice_id.reference if line.invoice_id.type in ('in_invoice', 'in_refund') else line.invoice_id.number,
                        })

class account_invoice_line(models.Model):
    _inherit = "account.invoice"

    @api.one
    def action_move_create(self):
        res = super(account_invoice_line, self).action_move_create()
        _logger.warn('invoice',self,'lines',self.invoice_line)
        #raise Warning('kalle')
        for l in self.invoice_line:
            self.env['account.analytic.default'].bom_account_create(l)
             
