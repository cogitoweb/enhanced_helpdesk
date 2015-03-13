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


class wizard_change_ticket_user(models.TransientModel):

    _name = "wizard.change.ticket.user"

    # ---- Fields

    user_id = fields.Many2one('res.users', required=True,
                              domain=[('partner_id.parent_id', '!=', False)])

    @api.multi
    def apply(self):
        res = {'type': 'ir.actions.act_window_close'}
        ticket = self.env['crm.helpdesk'].browse(
            self.env.context.get('active_id', False))
        if not ticket:
            return res
        # ----- Write new user in ticket
        ticket.request_id = self.user_id.id
        ticket.partner_id = self.user_id.partner_id.parent_id.id
        self.email_from = self.user_id.email
        # ----- Search the linked project task to update partner
        task = self.env['project.task'].search(
            [('ticket_id', '=', ticket.id)])
        if not task:
            return res
        task.partner_id = self.user_id.partner_id.parent_id.id
        return res
