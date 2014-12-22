# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Andre@ (<info@apuliasoftware.it>)
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


from openerp import models, fields, api, SUPERUSER_ID, _
from openerp.exceptions import Warning
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
            info = '<img height="40px" \
src="/web/binary/image?model=res.partner&id=%s&field=image_medium" \
/> %s - %s<br /><br />' % (msg.user_id.partner_id.id, msg.user_id.name, msg.date)
            info = '%s%s' % (info, msg.message)
            if len(msg.attachment_ids) > 0:
                info = '%s\n\n%s Attachment(s)' % (info,
                                                   len(msg.attachment_ids))
            if msg.user_id.signature:
                signature = msg.user_id.signature.replace('<br>', '\n')
                signature = BeautifulSoup(signature)
                info = '%s<br /><br />---\n%s' % (info, str(signature.text))
            msg.complete_message = info

    @api.onchange('message')
    def onchange_message(self):
        if self.message:
            self.complete_message = 'Message Preview\n\n%s' % (self.message)

    @api.multi
    def unlink(self):
        for qa in self:
            # ----- Impossible to delete other user's messages
            if qa.user_id.id != self.env.user.id:
                raise Warning(
                    _('Can not delete messages posted from other users'))
            # ----- Impossibile to delete messages with an answer
            if qa.search([('helpdesk_id', '=', qa.helpdesk_id.id),
                          ('id', '>', qa.id)]):
                raise Warning(
                    _('Can not delete messages with an answer'))
        return super(HelpdeskQA, self).unlink()

    @api.model
    def create(self, values):
        res = super(HelpdeskQA, self).create(values)
        # ----- Company Recordset
        company = self.env['res.users'].browse(SUPERUSER_ID).company_id
        # ---- Call a function to send mail
        #~ url = self.get_signup_url(res)
        if res.helpdesk_id.external_ticket_url:
            # ---- Send mail to user
            mail_to = ['"%s" <%s>' % (
                res.helpdesk_id.request_id.partner_id.name,
                res.helpdesk_id.email_from
                )]
        else:
            if res.helpdesk_id.user_id:
                # ---- Send mail to techinical support
                mail_to = ['"%s" <%s>' % (
                    res.helpdesk_id.user_id.name,
                    res.helpdesk_id.user_id.partner_id.email
                    )]
            else:
                # ---- Use company email
                mail_to = ['"%s" <%s>' % (company.name, company.email_ticket)]
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference(
            'enhanced_helpdesk', 'email_template_ticket_reply')[1] or False
        template = self.env['email.template']
        tmpl_br = template.sudo().browse(template_id)
        text = tmpl_br.body_html
        subject = tmpl_br.subject
        text = template.render_template(text, 'helpdesk.qa',
                                        res.id)
        subject = template.render_template(subject, 'helpdesk.qa',
                                           res.id)
        # ---- Get active smtp server
        mail_server = self.env['ir.mail_server'].sudo().search(
            [], limit=1, order='sequence')

        mail_value = {
            'body_html': text,
            'subject': subject,
            'email_from': company.email_ticket,
            'email_to': mail_to,
            'mail_server_id': mail_server.id,
            }
        msg = self.env['mail.mail'].sudo().create(mail_value)
        self.env['mail.mail'].sudo().send([msg.id])
        return res
