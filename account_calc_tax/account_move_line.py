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



class account_move_line(models.Model):
    _inherit = "account.move.line"

    def _calc_tax(self):
        calc_tax = self.env['ir.config_parameter'].get_param('account_calc_tax',default=False)
        if not calc_tax:
            calc_tax = '0.80'
            self.env['ir.config_par_ameter'].set_param('account_calc_tax',calc_tax)
        if self.debit > 0:
            self.debit = self.debit * float(calc_tax)
        if self.credit > 0:
            self.credit = self.credit * float(calc_tax)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
