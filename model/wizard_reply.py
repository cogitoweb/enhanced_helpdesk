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
from openerp import netsvc


class wizard_ticket_reply(models.TransientModel):

    _name = "wizard.ticket.reply"

    # ---- Fields

    ticket_id = fields.Many2one('crm.helpdesk')
    ticket_reply = fields.Text('Reply')
    attachment = fields.Binary('Attachment')
    attachment_name = fields.Char(size=64)
    flag_name = fields.Boolean()
    new_state = fields.Selection(related='ticket_id.state')

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

        # ---- write new value on ticket
        if not self.ticket_id.user_id:
            self.ticket_id.user_id = self._uid
        # ---- set new state to ticket
        if wkf_trigger:
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(self.env.user.id, 'crm.helpdesk',
                                    self.ticket_id.id,
                                    wkf_trigger, self._cr)
        # ----- close task if the ticket is closed
        if wkf_trigger == 'ticket_close':
            data_model = self.env['ir.model.data']
            state = data_model.get_object('project',
                                          'project_tt_deployment')
            tasks = self.env['project.task'].search(
                [('ticket_id', '=', self.ticket_id.id)])
            if tasks:
                for task in tasks:
                    task.stage_id = state.id
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def ticket_close(self):
        if self.new_state == 'pending':
            value = 'ticket_pending_done'
        elif self.new_state == 'open':
            value = 'ticket_working_done'
        else:
            value = 'ticket_close'
        return self.reply(wkf_trigger=value)

    @api.multi
    def ticket_working(self):
        if self.new_state == 'pending':
            value = 'ticket_pending_open'
        else:
            value = 'ticket_working'
        return self.reply(wkf_trigger=value)

    @api.multi
    def ticket_pending(self):
        if self.new_state == 'draft':
            value = 'ticket_pending'
        elif self.new_state == 'open':
            value = 'ticket_working_pending'
        return self.reply(wkf_trigger=value)

    @api.multi
    def ticket_cancel(self):
        return self.reply(wkf_trigger='ticket_cancel')

    @api.onchange('attachment')
    def onchange_attachment(self):
        if self.attachment:
            self.flag_name = True
        else:
            self.flag_name = False
