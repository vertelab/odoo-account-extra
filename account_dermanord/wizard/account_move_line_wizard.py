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
from openerp import api, models, fields, _
from openerp.exceptions import except_orm, Warning
import base64
from pyexcel_ods import save_data, get_data
from collections import OrderedDict
import tempfile
import os
import logging
_logger = logging.getLogger(__name__)


class show_journal_items_period_wizard(models.TransientModel):
    _name = 'show.journal.items.wizard.period'

    name = fields.Char()
    period_start = fields.Many2one(string='Period Start', comodel_name='account.period', required=True)
    period_stop = fields.Many2one(string='Period Stop', comodel_name='account.period', required=True)
    file_data = fields.Binary(string='File', readonly=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')

    @api.multi
    def generate_file(self):
        self.ensure_one()
        date_start = self.period_start.date_start
        date_stop = self.period_stop.date_stop
        if date_start > date_stop:
            raise Warning(_('Period Stop must be later than or same as period start.'))
        period_ids = self.env['account.period'].search([('date_start', '>=', date_start), ('date_stop', '<=', date_stop)])
        tax_code_ids = self._context.get('active_ids', [])
        data = OrderedDict()
        title = ['Name', 'Date', 'Entry', 'Period', 'Company', 'Account', 'Tax', 'Debit', 'Kredit']
        for tax_code_id in tax_code_ids:
            tax_account = self.env['account.tax.code'].browse(tax_code_id)
            move_lines = self.env['account.move.line'].search([('move_id.period_id', 'in', period_ids.mapped('id')), ('tax_code_id', '=', tax_code_id), ('move_id.state', '=', 'posted')])
            sheet = [title]
            credit = 0.0
            debit = 0.0
            for line in move_lines:
                sheet.append([line.name, line.date, line.move_id.name, line.move_id.period_id.name, line.partner_id.name, line.account_id.name, line.tax_code_id.name, float(line.debit), float(line.credit)])
                credit += float(line.credit)
                debit += float(line.debit)
            sheet.append(['Result', credit-debit])
            data.update({
                tax_account.name: sheet
            })

        f = tempfile.NamedTemporaryFile('w+b', suffix='.ods')
        save_data(f.name, data)
        save_data('/tmp/tax.ods', data)
        nf = open(f.name, 'rb')
        self.write({
            'state': 'get',
            'name': 'tax.ods',
            'file_data': base64.b64encode(nf.read())
        })
        f.close()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'show.journal.items.wizard.period',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

