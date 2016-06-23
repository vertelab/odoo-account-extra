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
import openerp.tools

import logging
_logger = logging.getLogger(__name__)



#~ def _get_param(param,value):
    #~ if not self.env['ir.config_parameter'].get_param(param):
        #~ self.env['ir.config_parameter'].set_param(param,value)
    #~ return self.env['ir.config_parameter'].get_param(param)

def get_config(param,msg):
    value = openerp.tools.config.get(param,False)
    if not value:
        raise Warning(_("%s (%s in /etc/odoo/openerp-server.conf)" % (msg,param)))
    return value

class account_analytic_account(models.Model):
    _inherit = "account.analytic.account"

    database_name = fields.Char(string="Database")
    database_size = fields.Float(string='DB-size')
    database_disk = fields.Float(string='DB-disk')
    database_backup = fields.Float(string='DB-backup')
    mailsize = fields.Float(string="Mail-size")
    total_size = fields.Float(string="Total-size")
    nbr_users = fields.Integer(string='Number of users')
    last_login = fields.Datetime(string='Last login')


    @api.one
    def check_database(self):
        import xmlrpclib
        import psycopg2
        import os
        
        if not self.database_name:
            return
        
        try:
            common = xmlrpclib.ServerProxy('%s/xmlrpc/2/common' % 'http://localhost:8069')
            uid = common.authenticate(self.database_name, 'admin', get_config('admin_passwd','Master password is missing'),{})
            models = xmlrpclib.ServerProxy('%s/xmlrpc/2/object' % 'http://localhost:8069')
        except xmlrpclib.Error as err:
            raise Warning(_("%s (server %s, db %s)" % (err, 'localhost', self.database_name)))

        res = models.execute_kw(self.database_name,uid,get_config('admin_passwd','Master password is missing'),'res.users','search', [[['active','=',True],['share','=',False]]],{})
        self.nbr_users = len(set(res)-set([1])) + 3
        res = models.execute_kw(self.database_name,uid,get_config('admin_passwd','Master password is missing'),'res.users','read', [list(set(res)-set([1]))])
        last_login = None
        for l in res:
            if l.get('login_date',None) > last_login:
                last_login = l.get('login_date')
        self.last_login = last_login
        _logger.error('res.users %s' % res)
        conn = psycopg2.connect(dbname=self.database_name, user='root', password=get_config('admin_passwd','Master password is missing'), host='localhost')
        cur = conn.cursor()
        cur.execute("select pg_database_size('%s')" % self.database_name)
        self.database_size = float(cur.fetchone()[0]) / 1024 / 1014 
        cur.close()
        conn.close()

        _logger.error('size %s' % (float(os.popen('du -s /var/lib/odoo/.local/share/Odoo/filestore/%s' % self.database_name).read().split('\t')[0]) / 1024))
        self.database_disk = (float(os.popen('du -s /var/lib/odoo/.local/share/Odoo/filestore/%s' % self.database_name).read().split('\t')[0]) / 1024)
        #self.database_disk = sum(os.path.getsize(f) for f in [os.listdir('/var/lib/odoo/.local/share/Odoo/filestore/%s/%s' % (self.database_name,d)) for d in os.listdir('/var/lib/odoo/.local/share/Odoo/filestore/%s' % self.database_name)])
        companies = models.execute_kw(self.database_name,uid,get_config('admin_passwd','Master password is missing'),'res.company','search', [[]],{})
        self.mailsize = sum([float(c.get('total_quota',0.0)) for c in models.execute_kw(self.database_name,uid,get_config('admin_passwd','Master password is missing'),'res.company','read', [companies])])
        self.database_backup = ((os.path.getsize('/var/backups/%s.sql.gz' % self.database_name) / 1024 / 1024) + self.database_size + self.database_disk + self.mailsize) * 2
        self.total_size = round(self.mailsize + self.database_backup + self.database_disk + self.database_size) + 2048
        
        #raise Warning(len(self.recurring_invoice_line_ids.filtered(lambda r: r.product_id.id == self._product_extra_users())))
        invoice_lines = []
        product_extra_users = self.env['product.product'].browse(self._product_extra_users())
        if self.nbr_users > 1 and len(self.recurring_invoice_line_ids.filtered(lambda r: r.product_id.id == product_extra_users.id))==0:
            invoice_lines.append((0,0,{
                'product_id': product_extra_users.id,
                'name': "Extra användare",
                'price_unit': product_extra_users.list_price,
                'uom_id': product_extra_users.uom_id.id,
                'quantity': 1.0,
            }))
        product_extra_space = self.env['product.product'].browse(self._product_extra_space())
        if self.total_size > 1024.0 and len(self.recurring_invoice_line_ids.filtered(lambda r: r.product_id.id == product_extra_space.id))==0:
            invoice_lines.append((0,0,{
                'product_id': product_extra_space.id,
                'name': "Extra användare",
                'price_unit': product_extra_space.list_price,
                'uom_id': product_extra_space.uom_id.id,
                'quantity': 1.0,
            }))

        self.recurring_invoice_line_ids = invoice_lines

    @api.v8
    def _product_extra_users(self):
        res = self.pool['product.product'].search([('name','ilike','extra anv%')]) # Extra anv%
        if len(res)>0:
            return res[0].id
        else:
            return None
    @api.v7
    def _product_extra_users(self,cr,uid,context=None):
        res = self.pool['product.product'].search(cr,uid,[('name','ilike','extra anv%')]) # Extra anv%
        if len(res)>0:
            return res[0]
        else:
            return None
    @api.v8
    def _product_extra_space(self):
        res = self.env['product.product'].search([('name','=',u'Extra utrymme')])
        if len(res)>0:
            return res[0].id
        else:
            return None
    @api.v7
    def _product_extra_space(self,cr,uid,context=None):
        res = self.pool['product.product'].search(cr,uid,[('name','=',u'Extra utrymme')])
        if len(res)>0:
            return res[0]
        else:
            return None
            
    def _prepare_invoice_lines(self, cr, uid, contract, fiscal_position_id, context=None):
        fpos_obj = self.pool.get('account.fiscal.position')
        fiscal_position = None
        if fiscal_position_id:
            fiscal_position = fpos_obj.browse(cr, uid,  fiscal_position_id, context=context)
        invoice_lines = []
        self.check_database(cr,uid,[])
        for line in contract.recurring_invoice_line_ids:
            values = self._prepare_invoice_line(cr, uid, line, fiscal_position, context=context)
            product = self.pool['product.product'].browse(cr,uid,values['product_id'],context=context)
            if product.list_price <> values['price_unit']:
                values['discount'] = round((product.list_price - values['price_unit']) / product.list_price * 100)  
                values['price_unit'] = product.list_price
            if contract.nbr_users > 1 and values['product_id'] == self._product_extra_users(cr,uid):
                values['quantity'] = contract.nbr_users - 1 # every extra user
            if contract.total_size > 1024.0 and values['product_id'] == self._product_extra_space(cr,uid):
                import math
                values['quantity'] = math.ceil(contract.total_size / 1024.0) -1.0  # every started GB except the first
            invoice_lines.append((0, 0, values))            
        return invoice_lines
