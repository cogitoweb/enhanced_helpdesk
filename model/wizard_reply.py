# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp import models, fields, api
from openerp import workflow
import logging
#Get the logger
_logger = logging.getLogger(__name__)


class wizard_ticket_reply(models.TransientModel):

    _name = "wizard.ticket.reply"
    
    def _get_request_user_default(self):
        
        if(self.task_user_id):
            return self.task_user_id
        
        return self.env.user

    # ---- Fields

    ticket_id = fields.Many2one('crm.helpdesk')
    ticket_status_id = fields.Many2one('helpdesk.ticket.status', related='ticket_id.ticket_status_id',readonly=True)  
    ticket_reply = fields.Text('Reply')
    attachment = fields.Binary('Attachment')
    attachment_name = fields.Char(size=64)
    proxy_status_code = fields.Char(related='ticket_status_id.status_code')
    proxy_categ_emerg = fields.Boolean(related='ticket_id.categ_id.emergency')
    task_id = fields.Many2one('project.task', related='ticket_id.task_id',readonly=True) 
    points = fields.Integer(string='Points', related='task_id.points') 
    task_user_id = fields.Many2one('res.users',
                                 required=True,
                                 string='Assigned to', 
                                 default=_get_request_user_default,
                                 related='task_id.user_id') 
    deadline = fields.Date(string='Deadline', related='task_id.date_deadline')

    @api.multi
    def reply(self, context=None, wkf_trigger=''):
        if self.ticket_reply:
            value = {
                'message': self.ticket_reply,
                'helpdesk_id': self.ticket_id.id,
                'user_id': self._uid,
                }
            reply_id = self.env['helpdesk.qa'].create(value)

            if self.attachment:
                attach_value = {
                    'name': self.attachment_name,
                    'db_datas': self.attachment,
                    'res_model': 'helpdesk.qa',
                    'res_id': reply_id.id,
                    'helpdesk_qa_id': reply_id.id,
                    }
                self.env['ir.attachment'].create(attach_value)

            # ---- send mail to support for the new reply to ticket
            self.env['crm.helpdesk'].send_notification_mail(
                template_xml_id='email_template_ticket_reply',
                object_class='helpdesk.qa', object_id=reply_id.id)

        # ---- write new value on ticket
        if not self.ticket_id.user_id:
            self.ticket_id.user_id = self._uid
            
        _logger.info('try validate workflow %s', wkf_trigger)
            
        # ---- set new state to ticket
        if wkf_trigger:
            workflow.trg_validate(self._uid, 
                                  'crm.helpdesk', 
                                  self.ticket_id.id, 
                                  wkf_trigger, self._cr)

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def ticket_assigned(self):
        return self.reply(wkf_trigger='ticket_assigned')
    
    @api.multi
    def ticket_pending(self):
        return self.reply(wkf_trigger='ticket_quoted')
    
    @api.multi
    def ticket_working(self):
        return self.reply(wkf_trigger='ticket_approved')
    
    @api.multi
    def ticket_emerg(self):
        return self.reply(wkf_trigger='ticket_emerg')
    
    @api.multi
    def ticket_delivered(self):
        return self.reply(wkf_trigger='ticket_delivered')
    
    @api.multi
    def ticket_completed(self):
        return self.reply(wkf_trigger='ticket_completed')
