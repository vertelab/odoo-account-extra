# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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

class project_issue(models.Model):
    _inherit = 'project.issue'

    voucher_type = fields.Selection(selection_add=[('bankstatement','Bank Statement')])

    @api.multi
    def bankstatement(self,):
        statements = []
        for issue in self:
            record = self.env['account.bank.statement.import'].with_context({'journal_type':'bank'}).default_get(['journal_id','date','period_id'])
            record['data_file'] = self.env['ir.attachment'].search([('res_model','=',issue._name),('res_id','=',issue.id)])[0].datas
            statement = self.env['account.bank.statement.import'].create(record)
        result = self.env.ref('account_bank_statement_import.action_account_bank_statement_import').read({'res_model','view_type','view_mode','view_id','search_view_id','domain','context','type'})[0]
        result.update({
            'target': 'new',
            'res_id': statement.id,
        })
        return result