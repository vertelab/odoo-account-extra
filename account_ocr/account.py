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
import logging

_logger = logging.getLogger(__name__)

#~ https://www.bankgirot.se/tjanster/inbetalningar/bankgiro-inbetalningar/handbocker/
#~ https://www.bankgirot.se/globalassets/dokument/exempelfiler/bankgiroinbetalningar/bankgiroinbetalningar_exempelfil_avtal-om-ocr-kontroll_sv.txt

class account_invoice(models.Model):
    _inherit = "account.invoice"

    ocr = fields.Char(string="OCR Number")

    @api.multi
    def action_move_create(self):
        super(account_invoice, self).action_move_create()
        sequence = self.env.ref('account_ocr.account_invoice_ocr_sequence')
        for inv in self:
            #~ c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
            ocr = sequence.next_by_id(sequence.id)
            ocr_check = str(int(ocr))
            inv.ocr = ocr + str((10 - (sum(map(lambda x: x%10 + int(x/10), map(lambda x,y: x*y, map(int, ocr_check), ([2,1]*len(ocr_check))[:len(ocr_check)]))) % 10)) % 10)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
