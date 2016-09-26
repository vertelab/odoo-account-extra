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
import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    invoice_interest_id = fields.Many2one(comodel_name='account.invoice')
    invoice_interest_ids = fields.One2many(comodel_name='account.invoice',inverse_name='invoice_interest_id')
    
    @api.multi
    def action_invoice_interest_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the invoice.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        product_interest = self.env.ref('account_invoice_intetest.product_product_invoice_interest')
        product_fee = self.env.ref('account_invoice_intetest.product_product_invoice_fee')
        interest_rate = 8.0 / 100.0
        invoices = {}

        for oldinvoice in self:
            invoice = self.env['account.invoice'].create(oldinvoice._prepare_invoice())
            invoice.invoice_interest_id = oldinvoice.id
            total_amount = oldinvoice.total_amount
            for payment in oldinvoice.payment_ids:
                days = fields.from_string(oldinvoice.date_due) - fields.from_string(payment.date)
                self.env['account.invoice.line'].create({
                    'invoice_id': invoice.id,
                    'name': product_interest.name + 'amount %f days %d' % (total_amount,days.days),
                    'sequence': 10,
                    'origin': oldinvoice.name,
                    'account_id': oldinvoice.account_id.id,
                    'price_unit': interest_rate / 365.0 * days.days * total_amount,
                    'quantity': 1.0,
                    'uom_id': product_interest.uom_id.id,
                    'product_id': product_interest.id,
                    #'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
                    'account_analytic_id': oldinvoice.account_analytic_id,    
                })
                total_amount -= payment.amount                
            self.env['account.invoice.line'].create({
                'invoice_id': invoice.id,
                'name': product_fee.name,
                'sequence': 20,
                'origin': oldinvoice.name,
                'account_id': product_fee.oldinvoice.account_id.id,
                'price_unit': product_fee.lst_price,
                'quantity': 1.0,
                'uom_id': product_fee.uom_id.id,
                'product_id': product_interest.id,
                #'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
                'account_analytic_id': oldinvoice.account_analytic_id,    
            })

            invoice.compute_taxes()

        return [inv.id for inv in invoices.values()]
        
        
    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': _('Overdue invoice'),
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.account_id.id,
            'partner_id': self.partner_id.id,
            'journal_id': journal_id,
            'currency_id': self.currency_id.id,
            'comment': self.comment,
            'payment_term_id': self.payment_term_id and self.payment_term_id.id or False,
            'fiscal_position_id': self.fiscal_position_id and self.fiscal_position_id.id or False,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id or False,
            'team_id': self.team_id and self.team_id.id or False,
        }
        return invoice_vals


