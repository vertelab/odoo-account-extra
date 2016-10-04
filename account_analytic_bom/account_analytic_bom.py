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

class account_analytic_default(models.Model):
    _inherit = 'account.analytic.default'

    bom_id = fields.Many2one(comodel_name='mrp.bom', string='BOM')

    @api.model
    def Xaccount_get(self,product_id=None, partner_id=None, user_id=None, date=None, company_id=None):
        res = super(account_analytic_default,self).account_get(product_id, partner_id, user_id, date, company_id)
        if res and res.bom_id:
            for p in res.bom_id.product_ids:
                pass
                #~ r = super(account_analytic_default,self).account_get(product_id=p.id, partner_id, user_id, date, company_id)

        return res

#~ class account_invoice_line(Models.model):
    #~ _inherit = "account.invoice.line"
    #~ _description = "Invoice Line"

    #~ account_analytic_ids = fields.Many2many(comodel_name='account.analytic.account')

    #~ @api.one
    #~ def product_id_change(product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, company_id=None):
        #~ res_prod = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type, partner_id, fposition_id, price_unit, currency_id=currency_id, company_id=company_id, context=context)
        #~ rec = self.pool.get('account.analytic.default').account_get(product, partner_id, uid, time.strftime('%Y-%m-%d'), company_id=company_id, context=context)
        #~ raise Warning(rec)

        #~ if rec:
            #~ res_prod['value'].update({'account_analytic_id': rec.analytic_id.id})
        #~ else:
            #~ res_prod['value'].update({'account_analytic_id': False})
        #~ return res_prod

class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    account_analytic_ids = fields.Many2many(comodel_name='account.analytic.account')

    # Method overridden to set the analytic account by default on criterion match
    @api.one
    def invoice_line_create(self):
        create_ids = super(sale_order_line, self).invoice_line_create()
        for line in self.env['account.invoice.line'].browse(create_ids):
            rec = self.env['account.analytic.default'].account_get(line.product_id.id if line.product_id else None, self.order_id.partner_id.id, self.order_id.user_id.id, time.strftime('%Y-%m-%d'))
            if len(rec)>1:
                line.write({'account_analytic_ids': [(6,0,[a.id for a in rec])]})
        return create_ids

class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    account_analytic_ids = fields.Many2many(comodel_name='account.analytic.account')

    @api.model
    def move_line_get_item(self, line):
        # super
        return {
            'type': 'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit': line.price_unit,
            'quantity': line.quantity,
            'price': line.price_subtotal,
            'account_id': line.account_id.id,
            'product_id': line.product_id.id,
            'uos_id': line.uos_id.id,
            'account_analytic_id': line.account_analytic_id.id,
            'taxes': line.invoice_line_tax_id,
        }


    @api.model
    def move_line_get(self, invoice_id):
        inv = self.env['account.invoice'].browse(invoice_id)
        currency = inv.currency_id.with_context(date=inv.date_invoice)
        company_currency = inv.company_id.currency_id

        res = []
        for line in inv.invoice_line:
            mres = self.move_line_get_item(line)
            mres['invl_id'] = line.id
            res.append(mres)
            tax_code_found = False
            taxes = line.invoice_line_tax_id.compute_all(
                (line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)),
                line.quantity, line.product_id, inv.partner_id)['taxes']
            for tax in taxes:
                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = tax['price_unit'] * line.quantity * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = tax['price_unit'] * line.quantity * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(dict(mres))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = currency.compute(tax_amount, company_currency)

        return res
