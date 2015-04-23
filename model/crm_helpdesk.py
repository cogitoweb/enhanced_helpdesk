# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Apulia (<info@apuliasoftware.it>)
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
import logging


_logger = logging.getLogger(__name__)


class CrmHelpdesk(models.Model):

    _inherit = "crm.helpdesk"
    _rec_name = 'display_name'

    # ---- Fields
    request_id = fields.Many2one('res.users',
                                 required=True,
                                 string='Richiedente',
                                 default=lambda self: self.env.user)
    external_ticket_url = fields.Char(compute='_get_external_ticket_url')
    helpdesk_qa_ids = fields.One2many('helpdesk.qa', 'helpdesk_id')
    attachment_ids = fields.One2many('ir.attachment',
                                     'crm_helpdesk_id')
    display_name = fields.Char(string='Ticket',
                               compute='_compute_display_name',)
    related_ticket = fields.Html()

    _track = {
        'state': {
            'enhanced_helpdesk.open':
            lambda self, cr, uid, obj, ctx=None: obj['state'] == 'open',
            'enhanced_helpdesk.pending':
            lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'enhanced_helpdesk.done':
            lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
            'enhanced_helpdesk.cancel':
            lambda self, cr, uid, obj, ctx=None: obj['state'] == 'cancel',
        },
    }

    @api.one
    @api.depends('name')
    def _compute_display_name(self):
        self.display_name = '#%s - %s' % (self.id, self.name)

    @api.multi
    def _get_external_ticket_url(self):
        for ticket in self:
            url = self.get_signup_url(ticket)
            self.external_ticket_url = url or ''

    def get_signup_url(self, ticket):
        user_logged = self.env.user.id
        partner = ticket.request_id.partner_id
        if user_logged == partner.id:
            return False
        action = 'enhanced_helpdesk.action_enhanced_helpdesk'
        partner.signup_prepare()
        val = partner._get_signup_url_for_action(
            action=action, view_type='form',
            res_id=ticket.id)[partner.id]
        return val

    @api.onchange('request_id')
    def onchange_requestid(self):
        _logger.info('BlaBlaCar')
        self.user_id = False
        if self.request_id:
            self.partner_id = self.request_id.partner_id.parent_id.id
            self.email_from = self.request_id.email

    @api.onchange('description')
    def onchange_description(self):
        self.related_ticket = '<br/><strong>Related Tickets</strong><br/> \
Remember to search your problem in old tickets before to open new one'

    @api.model
    def create(self, values):
        res = super(CrmHelpdesk, self).create(values)
        task_value = {
            'partner_id': values['partner_id'],
            'name': values['name'],
            'description': values['description'],
            'ticket_id': res.id,
            }
        self.env['project.task'].sudo().create(task_value)
        # ---- send mail to support for the new ticket
        company = self.env['res.users'].browse(SUPERUSER_ID).company_id
        mail_to = ['"%s" <%s>' % (company.name, company.email_ticket)]
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference(
            'enhanced_helpdesk', 'email_template_ticket_new')[1] or False
        template = self.env['email.template']
        tmpl_br = template.sudo().browse(template_id)
        text = tmpl_br.body_html
        subject = tmpl_br.subject
        text = template.render_template(text, 'crm.helpdesk',
                                        res.id)
        subject = template.render_template(subject, 'crm.helpdesk',
                                           res.id)
        # ---- Get active smtp server
        mail_server = self.env['ir.mail_server'].sudo().search(
            [], limit=1, order='sequence')
        # ---- adding text to reply
        text = '%s\n\n -- %s' % (text, res.description)

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

    @api.multi
    def close_ticket(self):
        self.write({'state': 'done'})

    @api.multi
    def cancel_ticket(self):
        self.write({'state': 'cancel'})

    @api.multi
    def reopen_ticket(self):
        self.write({'state': 'draft'})

    @api.multi
    def working_ticket(self):
        self.write({'state': 'open'})

    @api.multi
    def pending_ticket(self):
        self.write({'state': 'pending'})
