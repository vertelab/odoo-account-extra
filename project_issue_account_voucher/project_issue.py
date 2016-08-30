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

import logging
_logger = logging.getLogger(__name__)

class project_issue(models.Model):
    _inherit = 'project.issue'

    voucher_type = fields.Selection(selection_add=[('voucher_in','Supplier Voucher'),('voucher_out','Customer Voucher')],)

    @api.multi
    def voucher_in(self,):
        vouchers = []
        for issue in self:
            voucher = self.env['account.voucher'].create({
                'origin': '%s (%d)' % (issue.name,issue.id),
                'type': 'purchase',
                'comment': issue.description,
                'company_id': issue.company_id.id,
                'user_id': issue.user_id.id,
                'account_id': issue.partner_id.property_account_receivable.id,
                'partner_id': issue.partner_id.id,
            })
            issue._finnish(voucher,_('Supplier voucher created'))
            vouchers.append(voucher)
        return self._get_views(voucher,'account_voucher.view_voucher_tree')

    @api.multi
    def voucher_out(self,):
        vouchers = []
        for issue in self:
            voucher = self.env['account.voucher'].create({
                'origin': '%s (%d)' % (issue.name,issue.id),
                'type': 'sale',
                'comment': issue.description,
                'company_id': issue.company_id.id,
                'user_id': issue.user_id.id,
                'account_id': issue.partner_id.property_account_receivable.id,
                'partner_id': issue.partner_id.id,
            })
            issue._finnish(voucher,_('Customer voucher created'))
            vouchers.append(voucher)
        return self._get_views(voucher,'account_voucher.view_voucher_tree')
