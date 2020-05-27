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
import openerp.tools as tools

import vatnumber

import logging
_logger = logging.getLogger(__name__)


class res_partner(models.Model):
    _inherit = 'res.partner'

    vat_date = fields.Datetime(string="VIES-kontroll")

    @api.one
    @api.depends('vat')
    def _vat_check(self):
        if self.vat:
            try:
                self.vat_check =  vatnumber.check_vies(self.vat)
            #~ except MethodNotFound,e:
                #~ raise Warning('Method missing %s' % e)
            except Exception,e:
                self.vat_check = e
                #raise Warning('Exception %s' % e)

    vat_check = fields.Char(string='VAT-check', compute='_vat_check',)  # store=True


    @api.one
    def check_vat(self):
        if not self.vat_subjected:
            return True
        res = super(res_partner,self).check_vat()
        if res:
           self.vat_date = fields.Datetime.now()
        return res


    def vat_change(self, cr, uid, ids, value, context=None):
        return {'value': {'vat_subjected': bool(value)}}

    @api.one
    def _construct_constraint_msg(self, cr, uid, ids, context=None):
        if not self.vat_subjected:
            return True
        return super(res_partner,self)._construct_constraint_msg()

class sale_order(models.Model):
    _inherit = 'sale.order'
    
    vat_date = fields.Datetime(related="partner_id.vat_date", required=True)
    
   
    
    @api.one
    def action_button_confirm(self):
        if not self.partner_id.check_vat():
           self.env['mail.message'].create({
                    'body': _("VIES-check error %s" % self.vat_check),
                    'subject': "Exception",
                    'author_id': self.env['res.users'].browse(self.env.uid).partner_id.id,
                    'res_id': self.id,
                    'model': self._name,
                    'type': 'notification',})
        return super(sale_order,self).action_button_confirm()
        
# ~ class account_fiscal_position_tax(models.Model):
    # ~ _inherit = 'account.fiscal.position.tax'

    # ~ vat_warning = fields.Boolean(string = "Warning check", help = "check valid VAT VIES-control") 
    
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
