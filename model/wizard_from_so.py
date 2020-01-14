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


class wizard_ticket_from_so(models.TransientModel):

    _name = "wizard.ticket.from.so"
    
    def _get_request_user_default(self):
        
        if(self.task_user_id):
            return self.task_user_id
        
        return self.env.user

    # ---- Fields

    order_id = fields.Many2one('sale.order')
    task_user_id = fields.Many2one('res.users',
                                 required=True,
                                 string='Assigned to', 
                                 default=_get_request_user_default) 
    deadline = fields.Date(string='Deadline')

    # ----- Methods    

    @api.multi
    def generate(self):

        self.ticket_generate(False)

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def generate_and_complete(self):

        self.ticket_generate(True)

        return {'type': 'ir.actions.act_window_close'}

    def ticket_generate(self, complete):

        # [TODO] TICKET CREATION if not created

        if complete:
            pass

        return True
