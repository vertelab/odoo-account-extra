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
from openerp import http
from openerp.http import request
from openerp import SUPERUSER_ID
from datetime import datetime
import werkzeug
import pytz
import base64
from openerp.tools import ustr
import urllib2


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

class website_project_issue(http.Controller):
        
    @http.route(['/project/issue/<model("project.issue"):issue>/attachement','/project/issue/new/attachement',], type='http', auth="user", website=True)
    def upload_attachement(self, issue=False, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        error = {}
        user = request.env['res.users'].browse(uid)
        if not issue and request.httprequest.method == 'POST':
            issue = request.env['project.issue'].create({'partner_id': user.partner_id.id, 'name': post.get('name'), 'description': post.get('description')})
        if issue and request.httprequest.method == 'POST':
            issue.write({'partner_id': user.partner_id.id, 'name': post.get('name'), 'description': post.get('description')})
        
        if request.httprequest.method == 'POST' and post.get('ufile'):
            _logger.debug("This is attachement post %s /issue/nn" % (post))
            request.env['ir.attachment'].create({
                    'name': post['ufile'].filename,
                    'res_name': issue.name,
                    'res_model': 'project.issue',
                    'res_id': issue.id,
                    'datas': base64.encodestring(post['ufile'].read()),
                    'datas_fname': post['ufile'].filename,
                })
                
        
        return request.website.render("website_project_issue.upload_attachement", {
                'issue': issue,
                'error': error,
                'attachements': issue and request.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]) or False,
            })
        
        
    @http.route(['/file/<model("ir.attachment"):file>',], type='http', auth='user')
    def file_download(self, file=False, **kw):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        return request.make_response(base64.b64decode(file.datas),
                [('Content-Type', file.mimetype),
                 ('Content-Disposition', content_disposition(file.name))])
  
