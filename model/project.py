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
    ticket_display_id = fields.Char(string='Ticket ID', related='ticket_id.display_id')
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
                                     ('pending', 'Pending'),
                                     ('open', 'In Progress'),
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

class Project(models.Model): 
    
    _inherit = 'project.project'
    
    # il campo di riferimento è 
    ### invoiced_hours su task
    ### invoiced_hours su issue
    total_billable_hours = fields.Float(compute='compute_total_billable_hours', store=True)
    used_billable_hours = fields.Float(compute='compute_total_billable_hours', store=True)
    locked_billable_hours = fields.Float(compute='compute_total_billable_hours', store=True)
    free_billable_hours = fields.Float(compute='compute_total_billable_hours', store=True)
    
    @api.depends('tasks.invoiced_hours')
    def compute_total_billable_hours(self):
        for record in self:
            
            ## one liner
            # sum(task.invoiced_hours for task in record.tasks)
            
            tot = 0
            used = 0
            locked = 0
            free = 0
            
            for task in record.tasks:
                
                if task.invoiced_hours > 0:
                    if task.stage_id.name in ['Analysis', 'Specification', 'Design', 'Development', 'Testing', 'Merge',
                        'Waiting Response', 'Waiting Instructions', 'Suspended']:
                        locked = locked + task.invoiced_hours
                    elif task.stage_id.name in ['Done']:
                        used = used + task.invoiced_hours
                elif task.invoiced_hours < 0:
                    if task.stage_id.name in ['Done']:
                            tot = tot - task.invoiced_hours

            free = tot - (used + locked)
            
            record.total_billable_hours = tot
            record.used_billable_hours = used
            record.locked_billable_hours = locked
            record.free_billable_hours = free