# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Andre@ (<a.gallina@cgsoftware.it>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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


from openerp import models, fields, api, SUPERUSER_ID
from BeautifulSoup import BeautifulSoup


class IrAttachment(models.Model):

    _inherit = 'ir.attachment'

    helpdesk_qa_id = fields.Many2one('helpdesk.qa')


class HelpdeskQA(models.Model):

    _name = 'helpdesk.qa'

    # ---- Fields
    message = fields.Text('Message')
    helpdesk_id = fields.Many2one('crm.helpdesk')
    date = fields.Datetime(string='Message Date', default=fields.Date.today())
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    complete_message = fields.Text(compute='_complete_message')
    attachment_ids = fields.One2many('ir.attachment',
                                     'helpdesk_qa_id')

    @api.multi
    def _complete_message(self):
        for msg in self:
            info = '%s - %s\n\n' % (msg.user_id.name, msg.date)
            info = '%s%s' % (info, msg.message)
            if len(msg.attachment_ids) > 0:
                info = '%s\n\n%s Attachment(s)' % (info,
                                                   len(msg.attachment_ids))
            if msg.user_id.signature:
                signature = msg.user_id.signature.replace('<br>', '\n')
                signature = BeautifulSoup(signature)
                info = '%s\n\n---\n%s' % (info, str(signature.text))
            msg.complete_message = info

    @api.onchange('message')
    def onchange_message(self):
        if self.message:
            self.complete_message = 'Message Preview\n\n%s' % (self.message)

    @api.model
    def create(self, values):
        res = super(HelpdeskQA, self).create(values)
        # ---- call a function to send mail
        url = self.get_signup_url(res)
        if url:
            # ---- send mail to user
            mail_to = ['"%s" <%s>' % (
                res.helpdesk_id.request_id.partner_id.name,
                res.helpdesk_id.email_from
                )]
        else:
            if res.helpdesk_id.user_id:
                # ---- send mail to techinical support
                mail_to = ['"%s" <%s>' % (
                    res.helpdesk_id.user_id.name,
                    res.helpdesk_id.user_id.partner_id.email
                    )]
            else:
                # ---- get email from company
                company = self.env['res.users'].browse(SUPERUSER_ID).company_id
                mail_to = ['"%s" <%s>' % (company.name, company.email_ticket)]
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference(
            'enhanced_helpdesk', 'email_template_ticket_reply')[1] or False
        template = self.env['email.template']
        tmpl_br = template.browse(template_id)
        text = tmpl_br.body_html
        subject = tmpl_br.subject
        text = template.render_template(text, 'crm.helpdesk',
                                        res.helpdesk_id.id)
        subject = template.render_template(subject, 'crm.helpdesk',
                                           res.helpdesk_id.id)

        # ---- Get active smtp server
        mail_server = self.env['ir.mail_server'].sudo().search(
            [], limit=1, order='sequence')
        # ---- adding text to reply

        text = '%s\n\n -- %s' % (text, res.complete_message)

        text = "%s<br/> <a href='%s'>Accedi alla risposta</a>" % (text, url)
        mail_value = {
            'body_html': text,
            'subject': subject,
            'email_from': 'support@apuliasoftware.it',
            'email_to': mail_to,
            'mail_server_id': mail_server.id,
            }
        msg = self.env['mail.mail'].sudo().create(mail_value)
        self.env['mail.mail'].sudo().send([msg.id])
        return res

    def get_signup_url(self, record):
        user_logged = self._uid
        partner = record.helpdesk_id.request_id.partner_id
        if user_logged == record.helpdesk_id.request_id.id:
            return False
        action = 'enhanced_helpdesk.action_enhanced_helpdesk'
        partner.signup_prepare()
        val = partner._get_signup_url_for_action(
            action=action, view_type='form',
            res_id=record.helpdesk_id.id)[partner.id]
        return val
