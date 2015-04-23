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

from openerp import models, fields, api


class Task(models.Model):

    _inherit = 'project.task'

    # ----- Fields
    ticket_id = fields.Many2one('crm.helpdesk')
    rel_helpdesk_qa_ids = fields.One2many(string='Messages',
                                          related='ticket_id.helpdesk_qa_ids',
                                          readonly=True)
    ticket_last_answer_user_id = fields.Many2one(
        'res.users', compute='compute_ticket_last_answer',
        string="Last Answer User")
    ticket_last_answer_date = fields.Datetime(
        compute='compute_ticket_last_answer',
        string="Last Answer Date")
    ticket_state = fields.Selection([('draft', 'New'),
                                     ('open', 'In Progress'),
                                     ('pending', 'Pending'),
                                     ('done', 'Closed'),
                                     ('cancel', 'Cancelled')],
                                    related='ticket_id.state',
                                    string='Ticket State')

    @api.multi
    def compute_ticket_last_answer(self):
        for task in self:
            user_id = False
            date = False
            # ----- Keep the user from the last answer
            if task.rel_helpdesk_qa_ids:
                answer = task.rel_helpdesk_qa_ids[-1]
                user_id = answer.user_id.id
                date = answer.date
            task.ticket_last_answer_user_id = user_id
            task.ticket_last_answer_date = date
