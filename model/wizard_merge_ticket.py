# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Apulia Software S.r.l. (<info@apuliasoftware.it>)
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

from openerp import models, fields, api
from openerp import netsvc


class wizard_merge_ticket(models.TransientModel):

    _name = "wizard.merge.ticket"

    destination_ticket_id = fields.Many2one('crm.helpdesk', required=True)

    @api.multi
    def do_merge(self):
        ticket_id = self.env.context['active_id']
        ticket = self.env['crm.helpdesk'].browse(ticket_id)
        # ----- Cancel ticket and create relation with destination ticket
        ticket.merge_ticket_id = self.destination_ticket_id.id
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(self.env.user.id, 'crm.helpdesk',
                                ticket.id,
                                'ticket_cancel', self._cr)
        return {'type': 'ir.actions.act_window_close'}
