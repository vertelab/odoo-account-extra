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
from openerp.exceptions import except_orm, Warning, RedirectWarning
import datetime
#from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    invoice_interest_id = fields.Many2one(comodel_name='account.invoice')
    invoice_interest_ids = fields.One2many(comodel_name='account.invoice',inverse_name='invoice_interest_id')
    
    @api.multi
    def action_invoice_interest_create(self):
        """
        Create the invoice associated to the invoice.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        product_interest = self.env.ref('account_invoice_interest.product_product_invoice_interest')
        product_fee = self.env.ref('account_invoice_interest.product_product_invoice_fee')
        interest_rate = 8.0 / 100.0
        invoices = {}

        for oldinvoice in self:
            invoice = self.env['account.invoice'].create(oldinvoice._prepare_invoice())
            invoice.invoice_interest_id = oldinvoice.id
            amount_total = oldinvoice.amount_total
            date_due = oldinvoice.date_due
            for payment in oldinvoice.payment_ids.sorted(key=lambda p: p.date):
                days =  fields.Date.from_string(payment.date) - fields.Date.from_string(date_due) 
                self.env['account.invoice.line'].create({
                    'invoice_id': invoice.id,
                    'name': product_interest.name + 'amount %5.2f %s - %s %d days' % (amount_total,date_due,payment.date,days.days),
                    'sequence': 10,
                    'origin': oldinvoice.name,
                    'account_id': product_interest.property_account_income.id,
                    'price_unit': interest_rate / 365.0 * days.days * amount_total,
                    'quantity': 1.0,
                    'uom_id': product_interest.uom_id.id,
                    'product_id': product_interest.id,
                    #'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
                    #'account_analytic_id': oldinvoice.account_analytic_id,    
                })
                amount_total += payment.result
                date_due = payment.date

                _logger.warn(payment.read())       
            
#            for followup in oldinvoice.proforma_followup_history_ids:
#            _logger(followup.read())
            self.env['account.invoice.line'].create({
                'invoice_id': invoice.id,
                'name': product_fee.name,
                'sequence': 20,
                'origin': oldinvoice.name,
                'account_id': product_fee.property_account_income.id,
                'price_unit': product_fee.lst_price,
                'quantity': 1.0, # len(odlinvoice.proforma_followup_history_ids) + 0.0 if len(odlinvoice.proforma_followup_history_ids) > 1.0   else 1.0,
                'uom_id': product_fee.uom_id.id,
                'product_id': product_interest.id,
                #'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
                #'account_analytic_id': oldinvoice.account_analytic_id,    
            })

            #invoice.compute_taxes()
        (model,act_window_id) = self.env['ir.model.data'].get_object_reference('account', 'invoice_tree')
        act_window = self.env[model].browse(act_window_id)
        result = act_window.read()[0]
        result['domain'] = "[('id','in',[" + ','.join(map(str, [inv.id for inv in invoices.values()])) + "])]"
        return result
#        return [inv.id for inv in invoices.values()]
            #~ res = mod_obj.get_object_reference(cr, uid, 'purchase', 'purchase_order_form')
            #~ result['views'] = [(res and res[1] or False, 'form')]
            #~ result['res_id'] = purchase_ids and purchase_ids[0] or False
    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['sale.order'].default_get(['journal_id']).get('journal_id') or self.journal_id.id
        if not journal_id:
            raise Warning(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': _('Overdue invoice'),
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.account_id.id,
            'partner_id': self.partner_id.id,
            'journal_id': journal_id,
            'currency_id': self.currency_id.id,
            'comment': self.comment,
            'payment_term': self.payment_term.id if self.payment_term else False,
            'fiscal_position': self.fiscal_position and self.fiscal_position.id or False,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id or False,
        }
        return invoice_vals
