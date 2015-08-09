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

import logging
_logger = logging.getLogger(__name__)

class website_project_issue(http.Controller):
        
    @http.route(['/project/issue/<model("project.issue"):issue>/attachement','/project/issue/new/attachement',], type='http', auth="user", website=True)
    def upload_attachement(self, issue=False, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        error = {}
        default = {}
        if not issue:
            issue = request.env['ir.module.module'].create({'user_id': uid})

        _logger.error("website_project_issue-module issue %s /issue/nn" % (issue))

        
        if request.httprequest.method == 'POST' and post['ufile']:
            _logger.error("This is attachement post %s /issue/nn" % (post))
            env['ir.attachment'].create({
                    'name': post['ufile'].filename,
                    'res_name': issue.name,
                    'res_model': 'project.issue',
                    'res_id': issue.id,
                    'datas': base64.encodestring(post['ufile'].read()),
                    'datas_fname': post['ufile'].filename,
                })   
                

        return request.website.render("website_project_issue.upload_attachement", {
                'issue': issue,
                'post': post,
                'self': self,
                'error': error,
                'default': default,
            })
        
        #~ if module:
            #~ module_obj = request.env['ir.module.module'].search([('name','=',module)])[0]
        return 


#~ class product_template(models.Model):
    #~ _inherit = 'product.template'
    #~ 
    #~ quote_module_id = fields.Many2one('ir.module.module', string='Module')
