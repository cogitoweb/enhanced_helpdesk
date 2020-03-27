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
from openerp.tools.translate import _
from openerp import workflow
from openerp.exceptions import Warning
import math
from dateutil import parser

import logging
_logger = logging.getLogger(__name__)


class wizard_ticket_reply(models.TransientModel):

    _name = "wizard.ticket.reply.user"

    # ---- Fields
    ticket_id = fields.Many2one(
        'crm.helpdesk',
        required=True
    )
    ticket_status_id = fields.Many2one(
        'helpdesk.ticket.status', related='ticket_id.ticket_status_id',
        readonly=True
    )  
    ticket_reply = fields.Text(
        'Reply', 
        required=True
    )
    attachment = fields.Binary('Attachment')
    attachment_name = fields.Char(size=64)
    
    @api.multi
    def reply(self):

        reply_id = False
        message = self.ticket_reply

        value = {
            'message': message,
            'helpdesk_id': self.ticket_id.id,
            'user_id': self._uid,
            }
        reply_id = self.env['helpdesk.qa'].create(value)

        # ---- eventually attach
        if self.attachment:

            if not reply_id:
                reply_id = self.env['helpdesk.qa'].create(
                    {
                        'message': _('See attachment'),
                        'helpdesk_id': self.ticket_id.id,
                        'user_id': self._uid,
                    }
                )

            attach_value = {
                'name': self.attachment_name,
                'db_datas': self.attachment,
                'res_model': 'helpdesk.qa',
                'res_id': reply_id.id,
                'helpdesk_qa_id': reply_id.id,
                }
            self.env['ir.attachment'].create(attach_value)
        # --- end if

        return {'type': 'ir.actions.act_window_close'}
