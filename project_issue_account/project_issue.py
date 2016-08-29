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

import base64



import logging
_logger = logging.getLogger(__name__)

class project_issue(models.Model):
    _inherit = 'project.issue'

    voucher_project = fields.Boolean(related="project_id.use_voucher")
    voucher_type = fields.Selection(selection=[('in_invoice','Supplier Invoice'),('out_invoice','Customer Invoice'),('voucher_out','Customer Voucher'),('voucher_in','Supplier Voucher'),('bankstatement','Bank Statement'),('journal_entry','Journal Entry')])
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
            res = getattr(issue,issue.voucher_type)()
        return res

    def _do_message_post(self,object,text):
        self.message_post(body=_('%s <a href="http:/web#model=%s&id=%s">%s</a>' % (text,object._name,object.id,object.name)))   #   #model=<model>&id=<id>
        stages = self.env['project.task.type'].search([('project_ids','in',self.project_id.id)],order="sequence")
        if stages.filtered(lambda s: s.name == 'Done'):
            self.stage_id = stages.filtered(lambda s: s.name == 'Done').id
        else:
            self.stage_id = stages[-1].id
    def _do_move_attachment(self,object):
        for file in self.env['ir.attachment'].search([('res_model','=',self._name),('res_id','=',self.id)]):
            file.write({'res_model': object._name,'res_id': object.id })
        
    @api.multi
    def in_invoice(self,):
        invoices = []
        for issue in self:
            invoice = self.env['account.invoice'].create({
                'origin': '%s (%d)' % (issue.name,issue.id),
                'type': 'in_invoice',
                'comment': issue.description,
                'company_id': issue.company_id.id,
                'user_id': issue.user_id.id,
                'account_id': issue.partner_id.property_account_receivable.id,
                'partner_id': issue.partner_id.id,
            })
            issue._do_message_post(invoice,_('Supplier invoice created'))
            issue._do_move_attachment(invoice)
            invoices.append(invoice)
        result = self.env.ref('account.action_invoice_tree2').read()[0]
        result['views'] = [(self.env.ref('account.invoice_form').id,'form'),(self.env.ref('account.invoice_tree').id,'tree')]
        result['res_id'] = invoice.id # self.id
        result['search_view_id'] = self.env.ref("account.view_account_invoice_filter").id
      
        return result

    @api.multi
    def out_invoice(self,):
        invoices = []
        for issue in self:
            invoice = self.env['account.invoice'].create({
                'origin': '%s (%d)' % (issue.name,issue.id),
                'type': 'out_invoice',
                'comment': issue.description,
                'company_id': issue.company_id.id,
                'user_id': issue.user_id.id,
                'account_id': issue.partner_id.property_account_receivable.id,
                'partner_id': issue.partner_id.id,
            })
            issue._do_message_post(invoice,_('Customer invoice created'))
            issue._do_move_attachment(invoice)
            invoices.append(invoice)
        result = self.env.ref('account.action_invoice_tree1').read()[0]
        result['views'] = [(self.env.ref('account.invoice_form').id,'form'),(self.env.ref('account.invoice_tree').id,'tree')]
        result['res_id'] = invoice.id # self.id
        result['search_view_id'] = self.env.ref("account.view_account_invoice_filter").id
        return result

    @api.multi
    def voucher_in(self,):
        invoices = []
        for issue in self:
            invoice = self.env['account.voucher'].create({
                'origin': '%s (%d)' % (issue.name,issue.id),
                'type': 'purchase',
                'comment': issue.description,
                'company_id': issue.company_id.id,
                'user_id': issue.user_id.id,
                'account_id': issue.partner_id.property_account_receivable.id,
                'partner_id': issue.partner_id.id,
            })
            issue._do_message_post(invoice,_('Supplier voucher created'))
            issue._do_move_attachment(invoice)
            invoices.append(invoice)
        result = self.env.ref('account.action_invoice_tree2').read()[0]
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
            issue._do_message_post(move,_('Journal Entry created'))
            issue._do_move_attachment(move)
            moves.append(move)
        result = self.env.ref('account.view_move_line_tree').read()[0]
        result['views'] = [(self.env.ref('account.view_move_line_form').id,'form'),(self.env.ref('account.view_move_line_tree').id,'tree')]
        result['res_id'] = move.id # self.id
        #~ result['search_view_id'] = self.env.ref("account.view_move_line_tree_filter").id
        return result

    @api.multi
    def bankstatement(self,):
        statements = []
        for issue in self:
            record = self.env['account.bank.statement'].with_context({'journal_type':'bank'}).default_get(['journal_id','date','period_id'])
            #~ raise Warning(record)
            record.update(
            {
                'display_name': issue.name,
                'company_id': issue.company_id.id,
            })
            statement = self.env['account.bank.statement'].create(record)
            issue._do_message_post(statement,_('Bank statement created'))
            issue._do_move_attachment(statement)
            statements.append(statement)
        result = self.env.ref('account.view_bank_statement_tree').read()[0]  # Should be import wizard
        result['views'] = [(self.env.ref('account.view_bank_statement_form').id,'form'),(self.env.ref('account.view_bank_statement_tree').id,'tree')]
        result['res_id'] = statement.id # self.id
        result['search_view_id'] = self.env.ref("account.view_bank_statement_search").id
        return result

class project_project(models.Model):
    _inherit = 'project.project'

    use_voucher = fields.Boolean(string="Use Voucher")      


class account_move(models.Model):
    _inherit = 'account.move'
    image = fields.Binary(compute='_image')
    @api.one
    @api.depends('period_id')
    def _image(self):
        image = self.env['ir.attachment'].search([('res_model','=','account.move'),('res_id','=',self.id)])
        if image and image[0].mimetype == 'application/pdf':
            self.image = image[0].image
        elif image and image[0].mimetype in ['image/jpeg','image/png','image/gif']:
            self.image = image[0].datas
        else:
            self.image = None

class account_invoice(models.Model):
    _inherit = 'account.invoice'
    image = fields.Binary(compute='_image')
    @api.one
    @api.depends('period_id')
    def _image(self):
        image = self.env['ir.attachment'].search([('res_model','=','account.invoice'),('res_id','=',self.id)])
        if image and image[0].mimetype == 'application/pdf':
            self.image = image[0].image
        elif image and image[0].mimetype in ['image/jpeg','image/png','image/gif']:
            self.image = image[0].datas
        else:
            self.image = None



        
