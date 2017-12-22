# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Enterprise Management Solution, third party addon
#    Copyright (C) 2017 Vertel AB (<http://vertel.se>).
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

from odoo import api, models, fields, _
from odoo.exceptions import except_orm, Warning, RedirectWarning,MissingError

import logging
_logger = logging.getLogger(__name__)


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    image = fields.Binary(compute='_image')

    @api.one
    #~ @api.depends('period_id')
    def _image(self):
        image = self.env['ir.attachment'].search([('res_model','=','account.invoice'),('res_id','=',self.id)])
        if image and image[0].mimetype == 'application/pdf':
            self.image = image[0].image
        elif image and image[0].mimetype in ['image/jpeg','image/png','image/gif']:
            self.image = image[0].datas
        else:
            self.image = None

