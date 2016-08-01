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
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class pricelist_partnerinfo(models.Model):
    _inherit = 'pricelist.partnerinfo'

    price = fields.Float(string='Unit Price', required=True, digits_compute=dp.get_precision('Purchase Price'), help="This price will be considered as a price for the supplier Unit of Measure if any or the default Unit of Measure of the product otherwise")

class product_pricelist_item(models.Model):
    _inherit = 'product.pricelist.item'

    price_round = fields.Float(string='Price Roundings', required=True, digits_compute=dp.get_precision('Purchase Price'),
        help="Sets the price so that it is a multiple of this value.\n" \
        "Rounding is applied after the discount and before the surcharge.\n" \
        "To have prices that end in 9.9999, set rounding 10, surcharge -0.0001" \
        )

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    price_unit = fields.Float(string='Unit Price', required=True, digits_compute=dp.get_precision('Purchase Price'))
