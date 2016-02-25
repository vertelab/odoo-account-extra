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
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class account_move(models.Model):
    _inherit = "account.move"

    @api.one
    @api.depends('create_date')
    def _date_hour(self):
        self.date_hour = datetime.strptime(self.create_date,'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d-%H')
    
    date_hour = fields.Char(string="Hour",compute='_date_hour',store=True)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
