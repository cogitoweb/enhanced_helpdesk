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


class wizard_ticket_start_work(models.TransientModel):

    _name = "wizard.ticket.start_work"

    # ---- Fields
    ticket_id = fields.Many2one('crm.helpdesk')
    deadline = fields.Date(
        string='Deadline',
        related='ticket_id.task_id.date_deadline'
    )

    @api.multi
    def ticket_working(self):

        workflow.trg_validate(self._uid, 
                                  'crm.helpdesk', 
                                  self.ticket_id.id, 
                                  'ticket_work_direct', self._cr)

        return {'type': 'ir.actions.act_window_close'}
