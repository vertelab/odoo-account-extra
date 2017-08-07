# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
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
import base64
from cStringIO import StringIO

from subprocess import Popen, PIPE
import os
import tempfile
try:
    from xlrd import open_workbook, XLRDError
    from xlrd.book import Book
    from xlrd.sheet import Sheet
except:
    _logger.info('xlrd not installed. sudo pip install xlrd')

from lxml import html
import requests

import re

import logging
_logger = logging.getLogger(__name__)

try:
    import unicodecsv as csv
except:
    _logger.info('Missing unicodecsv. sudo pip install unicodecsv')


class DermanordPurchaseImport(models.TransientModel):
    _name = 'purchase.dermanord.import.wizard'

    order_file = fields.Binary(string='Order file')
    mime = fields.Selection([('html','text/html')])
    import_type = fields.Selection([('dustin','Dustin')])
    info = fields.Text(string='Info')
    tmp_file = fields.Char(string='Tmp File')
    
    @api.one
    @api.onchange('order_file')
    def check_file(self):
        self.mime = None
        self.import_type = None
        self.info = None
        self.tmp_file = None
        
        if self.order_file:
            fd, self.tmp_file = tempfile.mkstemp()
            os.write(fd, base64.b64decode(self.order_file))
            os.close(fd)

            try:
                pop = Popen(['file','-b','--mime',self.tmp_file], shell=False, stdout=PIPE)
                (result, _) = pop.communicate()
                read_mime = result.split(';')[0]
            except OSError,e:
                _logger.warning("Failed attempt to execute file. This program is necessary to check MIME type of %s", fname)
                _logger.debug("Trace of the failed MIME file attempt.", exc_info=True)
                raise Warning(e)

            self.mime = self.get_selection_text('mime',read_mime)
            
            if self.mime == 'html':
                tree = html.fromstring(base64.b64decode(self.order_file))
                data = tree.xpath('//tr/td/text()')

                if len(data)>48 and data[48] == '4600113259':
                    self.import_type = 'dustin'

                                        
            self.info = '%s\n%s' % (self.get_selection_value('import_type',self.import_type),self.get_selection_value('mime',self.mime))

        
    @api.multi
    def import_files(self):
        order = None
        missing_products = []                
        ordernummer = ''
        orderdatum = ''
        prodnr = re.compile('(\d{4}-\d{5})')

        if self[0].mime == 'html':
#
# Dustin
#
            if self.import_type == 'dustin':

                tree = html.fromstring(base64.b64decode(self.order_file))
                data = tree.xpath('//tr/td/text()')

                supplier = self.env['res.partner'].search([('name','=',self.get_selection_value('import_type',self.import_type)),('supplier','=',True)])
                customer = self.env['res.partner'].search([('name','=',u'Dermanord - Svensk Hudvård AB')])
                order = self.env['purchase.order'].create({
                    'partner_id': supplier.id,
                    'partner_ref': data[63],
                    'location_id': supplier.property_stock_customer.id,
                    'pricelist_id': supplier.property_product_pricelist_purchase.id,
                    'dest_address_id': customer.id,
                })
                i = 79
                while i < len(data):
                    prod = data[i]
                    ben  = data[i+1].strip().encode('iso-8859-1').decode('utf-8')
                    qty  = int(data[i+2].strip())
                    price_unit = float(data[i+3].strip().replace(' ','').replace('k','').replace('r',''))
                    #~ price_net = float(data[i+4].strip())

                    #~ product = self.env['product.product'].search([('default_code','=',prod)])
                    product = self.env['product.product'].search([('default_code','=',u'Inköp 5410')])
                    if not product:
                        self.env['product.product'].create({
                                    'name': u'Inköp 5410 förbrukningsmateriel',
                                    'default_code': u'Inköp 5410',
                                })
                

                    self.env['purchase.order.line'].create({
                                'order_id': order.id,
                                'product_id': product.id,
                                'price_unit': price_unit,
                                'product_qty': int(qty),
                                'name': ben,
                                'date_planned': data[61].strip(),
                            })
                    
                    i += 5
                    if data[i] == u'Varuv\xe4rde:':
                        i = len(data)
                
#
# END
#
        
        if missing_products and order:
            order.note = 'Saknade produkter: ' + ','.join(missing_products)
        if order:
            attachment = self.env['ir.attachment'].create({
                    'name': order.partner_ref  + '.' + self.mime,
                    'res_name': order.name,
                    'res_model': 'purchase.order',
                    'res_id': order.id,
                    'datas': self.order_file,
                    'datas_fname': order.partner_ref,
                })
            #~ if attachment.mimetype == 'application/pdf':
                #~ attachment.pdf2image(800,1200)

        return {'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_type': 'form',
                'view_mode': 'form',
                 'view_id': self.env.ref('purchase.purchase_order_form').id,
                 'res_id': order.id if order else None,
                 'target': 'current',
                 'context': {},
                 }


                                    
    def get_selection_text(self,field,value):
        for type,text in self.fields_get([field])[field]['selection']:
                if text == value:
                    return type
        return None

    def get_selection_value(self,field,value):
        for type,text in self.fields_get([field])[field]['selection']:
                if type == value:
                    return text
        return None
