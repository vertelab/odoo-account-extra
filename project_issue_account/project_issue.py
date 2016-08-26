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


import logging
_logger = logging.getLogger(__name__)

class project_issue_voucher_wizard(models.TransientModel):
    _name = 'project.issue.voucher.wizard'
    _description = 'Issue Voucher Wizard'

    memo = fields.Html(string='Note Content')
    #issue_ids = fields.One2many(comodel_name='project.issue', compute='_issue_ids')
    @api.one
    def _issue_ids(self):
        _logger.error('_get_issue %s' % self._context.get('active_ids', []))
        raise Warning(self._context.get('active_ids', []))
        self.issue_ids = self._context.get('active_ids', [])
    stage_id = fields.Many2one(comodel_name='project.category')
    voucher_type = fields.Selection(selection=[('invoice_in','Supplier Invoice'),('invoice_out','Customer Invoice'),('voucher_out','Customer Voucher'),('voucher_in','Supplier Voucher'),('bankstatement','Bank Statement'),('move','Journal Entry')])
    image = fields.Binary(compute='_image')
    @api.one
    @api.depends('memo')
    def _image(self):
        attachment = self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',self._context.get('active_ids', [])[0])])[0]
        self.image = attachment.datas

    @api.multi
    def create_voucher(self):
        _logger.error('Kalle')
        for n in self:
            for p in n.issue_ids:
                n.env['note.note'].create({
                    'memo': n.memo,
                    'partner_id': p.id,
                })



class project_issue(models.Model):
    _inherit = 'project.issue'

    voucher_project = fields.Boolean(related="project_id.voucher_project")
    voucher_type = fields.Selection(selection=[('in_invoice','Supplier Invoice'),('invoice_out','Customer Invoice'),('voucher_out','Customer Voucher'),('voucher_in','Supplier Voucher'),('bankstatement','Bank Statement'),('move','Journal Entry')])
    image = fields.Binary(compute='_image')
    @api.one
    @api.depends('project_id','email_from')
    def _image(self):
        image = self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',self.id)])
        if image:
            self.image = image[0].datas

    @api.multi
    def create_entry(self):
        for issue in self:
            res = getattr(issue,issue.voucher_type)()
        return res

    def _do_message_post(self,object,text):
        self.message_post(body=_('%s <a href="http:/web#model=%s&id=%s">%s</a>' % (text,object._name,object.id,object.name)))   #   #model=<model>&id=<id>
        self.state = 'done'
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
    def create_invoice_customer(self,):
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
            url = "<a href='/web?model=account.invoice&id=%d'>%s</a>" % (invoice.id,_('invoice'))
            issue.message_post(body=_('Customer %s created <a href="http:/web#model=%s&id=%s">Kalle</a>' % (invoice.type,invoice._name,invoice.id) ))   #   #model=<model>&id=<id>
         #   'body': _("{type} <a href='/web#model={model}&id={id}'>{message}</a> created\n").format(type=self.env.ref(edi_type).name,model=message._name,id=message.id,message=message.name),
                    

            for file in self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]):
                file.write({'res_model': 'account.invoice','res_id': invoice })
        return True

    @api.multi
    def create_invoice_supplier(self,):
        for issue in self:
            invoice = self.env['account.invoice'].create({
            'origin': issue.name,
            'type': 'in_invoice',
            'comment': issue.description,
            'company_id': issue.company_id.id,
            'user_id': issue.user_id.id,
            'account_id': issue.partner_id.property_account_payable.id,
            'partner_id': issue.partner_id.id,
            })
            for file in self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]):
                file.write({'res_model': 'account.invoice','res_id': invoice })
        return True

    @api.multi
    def create_move(self,):
        for issue in self:
            invoice = self.env['account.move'].create({
            'display_name': issue.name,
            'narration': issue.description,
            'company_id': issue.company_id.id,
            'to_check': True,
            })
            for file in self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]):
                file.write({'res_model': 'account.move','res_id': invoice })
        return True


    @api.multi
    def create_bank(self,):
        for issue in self:
            invoice = self.env['account.bank.statement'].create({
            'display_name': issue.name,
            'company_id': issue.company_id.id,
            })
            for file in self.env['ir.attachment'].search([('res_model','=','project.issue'),('res_id','=',issue.id)]):
                file.write({'res_model': 'account.bank.statement','res_id': invoice })
        return True
        
class project_project(models.Model):
    _inherit = 'project.project'

    voucher_project = fields.Boolean(string="Voucher")      
