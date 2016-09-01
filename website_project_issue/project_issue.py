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
from openerp import http
from openerp.http import request
from openerp import SUPERUSER_ID
from datetime import datetime
import werkzeug
import pytz
import base64
from openerp.tools import ustr
import urllib2
import re
import time

from wand.image import Image
from wand.display import display
from wand.color import Color
import subprocess


import logging
_logger = logging.getLogger(__name__)


def content_disposition(filename):
    filename = ustr(filename)
    escaped = urllib2.quote(filename.encode('utf8'))
    browser = request.httprequest.user_agent.browser
    version = int((request.httprequest.user_agent.version or '0').split('.')[0])
    if browser == 'msie' and version < 9:
        return "attachment; filename=%s" % escaped
    elif browser == 'safari':
        return u"attachment; filename=%s" % filename
    else:
        return "attachment; filename*=UTF-8''%s" % escaped


class ir_attachement(models.Model):
    _inherit='ir.attachment'
    
    image = fields.Binary()
    
    @api.multi
    def pdf2image(self,dest_width, dest_height):
        RESOLUTION    = 300
        #blob = self.datas.decode('base64')
        #raise Warning(self.base64_decode(self.datas))
        #str = self.datas + '=' *(-len(self.datas)%4)
        #img = Image(blob=self[0].datas.decode('base64'))
        #img.resize(dest_width,dest_height)        
        #~ self[0].image = img.make_blob(format='jpg').encode('base64')
        self[0].image = Image(blob=self[0].datas.decode('base64'),resolution=(RESOLUTION,RESOLUTION)).make_blob(format='jpg').encode('base64')
        #~ return 
        #~ try:
            #~ with Image(blob=self[0].datas.decode('base64'), resolution=(RESOLUTION,RESOLUTION)) as img:
                #~ img.background_color = Color('white')
                #~ img_width = img.width
                #~ ratio     = dest_width / img_width
                #~ img.resize(dest_width, dest_height)
    #~ #            img.format = 'jpeg'
                #~ self[0].image = img.make_blob(format='jpeg').encode('base64')
        #~ except Exception as e:
            #~ return None
        #    return None
            

class website_project_issue(http.Controller):
        
    @http.route(['/project/issue/<model("project.issue"):issue>/attachment','/project/issue/new/attachment', '/upload_voucher'], type='http', auth="user", website=True)
    def upload_attachement(self, issue=False, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        message = {}
        user = request.env['res.users'].browse(uid)
        voucher_name = [txt[1] for txt in request.env['project.issue'].fields_get(['voucher_type'])['voucher_type']['selection'] if txt[0] == 'in_invoice'][0]
        
        if not issue and request.httprequest.method == 'POST':
            try: 
                if len(post.get('name'))<1:
                    post['name'] = '%s %s' % (user.name,time.strftime("%x")) # Why?
                
                issue = request.env['project.issue'].create({'partner_id': user.partner_id.id, 
                                                             'name': '%s %s' % (voucher_name,post.get('name','')), 
                                                             'description': post.get('description'), 
                                                             'project_id': request.env['project.project'].search(['|',('partner_id','=',user.partner_id.id),(1,'=',1)])[0].id,
                                                             'voucher_type': post.get('voucher_type'),
                                                             })
            except Exception as e:
                message['danger'] = 'Could not create an issue %s' % e               
            
        if issue and request.httprequest.method == 'POST':
            issue.write({'partner_id': user.partner_id.id, 'name':  '%s %s' % (voucher_name,post.get('name','')), 'description': post.get('description')})
        
        if issue and request.httprequest.method == 'POST' and post.get('ufile'):
            _logger.debug("This is attachement post %s /issue/nn" % (post))  
            blob = post['ufile'].read()
            attachment = request.env['ir.attachment'].create({
                    'name': post['ufile'].filename,
                    'res_name': issue.name,
                    'res_model': 'project.issue',
                    'res_id': issue.id,
                    'datas': base64.encodestring(blob),
                    'datas_fname': post['ufile'].filename,
                })
            if attachment.mimetype == 'application/pdf':
                attachment.pdf2image(800,1200)
            message['success'] = _('Voucher uploaded %s (%s)' % (issue.name,issue.id))
        
        _logger.error("This is a %s and %s and %s, %s" % (type(issue),isinstance(issue,models.Model),issue,request.httprequest.url))
        return request.website.render("website_project_issue.upload_attachement", {
                'issue': False if re.search("upload_voucher",request.httprequest.url) is not None else issue,
                'message': message,
                'attachements': issue and request.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]) or False,
            })
        
        
    @http.route(['/file/<model("ir.attachment"):file>',], type='http', auth='user')
    def file_download(self, file=False, **kw):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        return request.make_response(base64.b64decode(file.datas),
                [('Content-Type', file.mimetype),
                 ('Content-Disposition', content_disposition(file.name))])
  
