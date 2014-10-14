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
    def reply(self):
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
        self.ticket_id.state = self.new_state
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('attachment')
    def onchange_attachment(self):
        if self.attachment:
            self.flag_name = True
        else:
            self.flag_name = False
