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
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

import logging
_logger = logging.getLogger(__name__)

class project_issue(models.Model):
    _inherit = 'project.issue'

    voucher_project = fields.Boolean(related="project_id.use_voucher")
    #~ voucher_type = fields.Selection(selection=[('in_invoice','Supplier Invoice'),('out_invoice','Customer Invoice'),('voucher_out','Customer Voucher'),('voucher_in','Supplier Voucher'),('bankstatement','Bank Statement'),('journal_entry','Journal Entry')])
    voucher_type = fields.Selection(selection=[('in_invoice', 'Supplier Invoice'),('out_invoice','Customer Invoice')], string='Voucher Type', default='in_invoice') #('journal_entry','Journal Entry')])
    image = fields.Binary(compute='_image')
    @api.one
    @api.depends('project_id','email_from')
    def _image(self):
        image = self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',self.id)])
        if image and image[0].mimetype == 'application/pdf':
            self.image = image[0].image
        elif image and image[0].mimetype in ['image/jpeg','image/png','image/gif']:
            self.image = image[0].datas
        else:
            self.image = None

    @api.multi
    def create_entry(self):
        for issue in self:
            if not issue.voucher_type:
                issue.voucher_type = 'in_invoice'
            res = getattr(issue,issue.voucher_type)()
        return res
    @api.one
    def _finnish(self,object,text):
        self.message_post(body=_('%s <a href="http:/web#model=%s&id=%s">%s</a>' % (text,object._name,object.id,object.name)))   #   #model=<model>&id=<id>
        self.stage_id = self.env.ref('project.project_stage_data_2').id
        for file in self.env['ir.attachment'].search([('res_model','=',self._name),('res_id','=',self.id)]):
            file.write({'res_model': object._name,'res_id': object.id })
    @api.model
    def _get_views(self,object,action,form=None,tree=None,kanban=None,graph=None,target='current'):
        result = self.env.ref(action).read({'res_model','view_type','view_mode','view_id','search_view_id','domain','context','type'})[0]
        #result = self.env.ref(action).read()[0]
        views = []
        view_mode = []
        if form:
            view_mode.append('form')
            views.append(((self.env.ref(form).id,'form')))
        if tree:
            view_mode.append('tree')
            views.append(((self.env.ref(tree).id,'tree')))
        if kanban:
            view_mode.append('kanban')
            views.append(((self.env.ref(kanban).id,'kanban')))
        if graph:
            view_mode.append('graph')
            views.append(((self.env.ref(graph).id,'graph')))
        result.update({
            'target': target,
            'res_id': object.id,
            'views': views,
            'view_mode': ','.join(view_mode)
        })
#        result['search_view_id'] = self.env.ref("account.view_account_invoice_filter").id
        #~ _logger.info('result %s' % result)
        return result

    @api.multi
    def in_invoice(self,): # vendor invoice
        invoices = []
        for issue in self:
            if not issue.partner_id:
                raise Warning(_('Please add a contact.'))
            invoice = self.env['account.invoice'].create({
                'origin': '%s (%d)' % (issue.name,issue.id),
                'type': 'in_invoice',
                'comment': issue.description,
                'company_id': issue.company_id.id,
                'user_id': issue.user_id.id,
                'account_id': issue.partner_id.property_account_payable_id.id,
                'partner_id': issue.partner_id.id,
                'journal_id': self.env['account.journal'].search([('type', '=', 'purchase')], order='sequence', limit=1).id or None,
            })
            issue._finnish(invoice,_('Supplier invoice created'))
            invoices.append(invoice)
        return self._get_views(invoice,'account.action_invoice_tree2',form='account.invoice_supplier_form') #,tree='account.action_invoice_tree2')
        result = self.env.ref('account.action_invoice_tree2').read()[0]
        result['views'] = [(self.env.ref('account.invoice_form').id,'form'),(self.env.ref('account.invoice_tree').id,'tree')]
        result['res_id'] = invoice.id # self.id
        result['search_view_id'] = self.env.ref("account.view_account_invoice_filter").id
        _logger.info('result %s' % result)
        return result

    @api.multi
    def out_invoice(self,): # customer invoice
        invoices = []
        for issue in self:
            if not issue.partner_id:
                raise Warning(_('Please add a contact.'))
            invoice = self.env['account.invoice'].create({
                'origin': '%s (%d)' % (issue.name,issue.id),
                'type': 'out_invoice',
                'comment': issue.description,
                'company_id': issue.company_id.id,
                'user_id': issue.user_id.id,
                'account_id': issue.partner_id.property_account_receivable.id,
                'partner_id': issue.partner_id.id,
                'journal_id': self.env['account.journal'].search([('type', '=', 'sale')], order='sequence', limit=1).id or None,
            })
            issue._finnish(invoice,_('Customer invoice created'))
            invoices.append(invoice)
        return self._get_views(invoice,'account.action_invoice_tree1',form='account.invoice_form')
        result['views'] = [(self.env.ref('account.invoice_form').id,'form'),(self.env.ref('account.invoice_tree').id,'tree')]
        result['res_id'] = invoice.id # self.id
        result['search_view_id'] = self.env.ref("account.view_account_invoice_filter").id
        return result


    @api.multi
    def journal_entry(self,):
        moves = []
        journal = self.env['account.journal'].search([('type','=','purchase')])[0]
        for issue in self:
            move = self.env['account.move'].create({
            'display_name': issue.name,
            'narration': issue.description,
            'company_id': issue.company_id.id,
            'journal_id': journal.id,
            'to_check': True,
            })
            issue._finnish(move,_('Journal Entry created'))
            moves.append(move)
        return self._get_views(move,'account.view_move_line_tree',form='account.view_move_line_form')
        result = self.env.ref('account.view_move_line_tree').read()[0]
        result['views'] = [(self.env.ref('account.view_move_line_form').id,'form'),(self.env.ref('account.view_move_line_tree').id,'tree')]
        result['res_id'] = move.id # self.id
        #~ result['search_view_id'] = self.env.ref("account.view_move_line_tree_filter").id
        return result

class project_project(models.Model):
    _inherit = 'project.project'

    use_voucher = fields.Boolean(string="Use Voucher")

class account_move(models.Model):
    _inherit = 'account.move'
    image = fields.Binary(compute='_image')
    @api.one
    #~ @api.depends('period_id')
    def _image(self):
        image = self.env['ir.attachment'].search([('res_model','=','account.move'),('res_id','=',self.id)])
        if image and image[0].mimetype == 'application/pdf':
            self.image = image[0].image
        elif image and image[0].mimetype in ['image/jpeg','image/png','image/gif']:
            self.image = image[0].datas
        else:
            self.image = None





