# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution, third party addon
# Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
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
{
'name': 'Account Dermanord',
'version': '0.1',
'summary': '',
'category': 'account,account_customer_no',
'description': """Extends invoice with more text .""",
'author': 'Vertel AB',
    'license': 'AGPL-3',
'website': 'http://www.vertel.se',
'sequence': 99,
'depends': ['report_intrastat', 'account_customer_no', 'stock', 'child_catagory_tags'],
'data': [
    'views/account_invoice_view.xml',
    'report_invoice.xml',
    'res_partner_view.xml',
    'stock_view.xml',
    'account_invoice_parcels_view.xml',
    'purchase_import_view.xml',
    'security/ir.model.access.csv',
    'wizard/account_move_line_wizard.xml',
],
'installable': True,
}
