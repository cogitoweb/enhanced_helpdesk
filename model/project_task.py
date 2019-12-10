# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Andre@ (<a.gallina@cgsoftware.it>)
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class Task(models.Model):

    _inherit = 'project.task'

    # ----- Fields
    ticket_id = fields.Many2one('crm.helpdesk')

    ticket_display_id = fields.Char(string='Ticket ID', related='ticket_id.display_id')
    rel_helpdesk_qa_ids = fields.One2many(string='Messages',
                                          related='ticket_id.helpdesk_qa_ids',
                                          readonly=True)
    ticket_last_answer_user_id = fields.Many2one(
        'res.users',
        related='ticket_id.last_answer_user_id',
        string="Last Answer User", readonly=True)
    
    ticket_last_answer_date = fields.Datetime(
        related='ticket_id.last_answer_date',
        string="Last Answer Date", readonly=True)

    ticket_state = fields.Many2one('helpdesk.ticket.status', related='ticket_id.ticket_status_id',readonly=True)
    
    
    @api.model
    def create(self, values):
        
        if not values.get('ticket_id', False):
            
            # check project
            project = self.env['project.project'].browse(values.get('project_id'))
            allow_creation = False
            
            if project and project.analytic_account_id:
                if project.analytic_account_id.account_type in ('CP', 'NS'):
                    allow_creation = True
            
            if not allow_creation:
                raise Warning(
                    _("I'm sorry, tasks without tickets can no longer be created "
                      "except on internal projects. Please check if you are on an internal project "
                      "or open a ticket.")
                             )

        return super(Task, self).create(values)
