# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2014 Vertel AB (<http://vertel.se>).
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
from openerp.osv import osv, fields


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner']

    name     = fields.Char('Name', required=True, select=True,track_visibility='onchange',)
    ref      = fields.Char('Contact Reference', select=1,track_visibility='onchange',)
    bank_ids = fields.One2many('res.partner.bank', 'partner_id', string='Banks', track_visibility='onchange',)
    website  = fields.Char('Website', track_visibility='onchange', help="Website of Partner or Company")
    comment  = fields.Text('Notes', track_visibility='onchange',)
    active   = fields.Boolean('Active', track_visibility='onchange',)
    function = fields.Char('Job Position',track_visibility='onchange',)
    type     = fields.Selection([('default', 'Default'), ('invoice', 'Invoice'),
                               ('delivery', 'Shipping'), ('contact', 'Contact'),
                               ('other', 'Other')], 'Address Type',track_visibility='onchange',
        help="Used to select automatically the right address according to the context in sales and purchases documents.")
    street  = fields.Char('Street',track_visibility='onchange',)
    street2 = fields.Char('Street2',track_visibility='onchange',)
    zip     = fields.Char('Zip', size=24,track_visibility='onchange', change_default=True)
    city    = fields.Char('City',track_visibility='onchange',)
    state_id = fields.Many2one("res.country.state", string='State', track_visibility='onchange',ondelete='restrict')

    country_id  = fields.Many2one('res.country', string='Country',track_visibility='onchange', ondelete='restrict')
    email   = fields.Char('Email',track_visibility='onchange',)
    phone   = fields.Char('Phone',track_visibility='onchange',)
    fax     = fields.Char('Fax',track_visibility='onchange',)
    mobile  = fields.Char('Mobile',track_visibility='onchange',)
#    birthdate = fields.Char('Birthdate',track_visibility='onchange',)
    is_company = fields.Boolean('Is a Company', track_visibility='onchange',help="Check if the contact is a company, otherwise it is a person")
    use_parent_address = fields.Boolean('Use Company Address', track_visibility='onchange',help="Select this if you want to set company's address information  for this contact")
    company_id = fields.Many2one('res.company', string='Company', track_visibility='onchange',select=1)
    user_ids = fields.One2many('res.users', 'partner_id', string='Users')
