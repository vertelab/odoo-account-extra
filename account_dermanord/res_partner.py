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

class res_partner(models.Model):
    _inherit ='res.partner'

    @api.multi
    def open_form(self):
        result = self.env.ref('base.view_partner_form').read()[0]
        result['views'] = [(self.env.ref('base.view_partner_form').id,'form'),(self.env.ref('base.view_partner_tree').id,'tree')]
        result['res_id'] = self.id # self.id
        result['search_view_id'] = self.env.ref("base.view_res_partner_filter").id
        return result

    incoterm = fields.Many2one(comodel_name='stock.incoterms', string='Incoterm', help='International Commercial Terms are a series of predefined commercial terms used in international transactions.')
    partner_ids = fields.Many2many(comodel_name='res.partner', relation='multi_partner', column1='partner_id', column2='parent_id', string='Multi Clients')

    @api.one
    @api.depends('category_id', 'child_ids', 'child_ids.category_id', 'partner_ids', 'partner_ids.category_id')
    def _get_childs_categs(self):
        if self.is_company:
            categories = self.env['res.partner.category'].browse([])
            for c in self.child_ids:
                for categ in c.category_id:
                    categories |= categ
            for p in self.partner_ids:
                for categ in p.category_id:
                    categories |= categ
            self.child_category_ids = categories


class multi_partner(models.Model):
    _name = 'multi.partner'

    parent_id = fields.Many2one(comodel_name='res.partner')
    partner_id = fields.Many2one(comodel_name='res.partner')
