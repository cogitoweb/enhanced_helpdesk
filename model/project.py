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
import logging
_logger = logging.getLogger(__name__)

###############################################################################
#
#
#
#
#
#
#




class Task(models.Model):

    _inherit = 'project.task'
    #_inherit = 'helpdesk.ticket.status' # Eredito il model degli stati altrimenti genera un errore


    # Functiont to populate fields.Select()
    # with ticket status coming from database
    @api.model
    def _get_ticket_status(self):
        lst=[]
        for status in self.env['helpdesk.ticket.status'].search([]):
            lst.append((status.id, status.status_name))
        return lst 

    # ----- Fields
    ticket_id = fields.Many2one('crm.helpdesk')
    #ticket_status = fields.Many2one('helpdesk.ticket.status') 


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

    # New ticket status are:
    # 1 = Nuovo
    # 2 = Preso in carico
    # 3 = In approvazione
    # 4 = In lavorazione
    # 5 = Consegna
    # 6 = Completato
    # 7 = Anullato
    #ticket_state = fields.Selection(selection=_get_ticket_status, related='ticket_status.id', string='Ticket State')                                



                               
                            
    points = fields.Integer(string='Points')                        

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
    ### points su task
    total_points = fields.Integer(compute='compute_total_points', store=True)
    used_points = fields.Integer(compute='compute_total_points', store=True)
    locked_points = fields.Integer(compute='compute_total_points', store=True)
    free_points = fields.Integer(compute='compute_total_points', store=True)
    
    @api.depends('tasks.points', 'tasks.stage_id')
    def compute_total_points(self):
        for record in self:
            
            ## one liner
            # sum(task.points for task in record.tasks)
            
            tot = 0
            used = 0
            locked = 0
            free = 0
            
            for task in record.tasks:
                
                if task.points > 0:
                    if task.stage_id.name in ['Analysis', 'Specification', 'Design', 'Development', 'Testing', 'Merge',
                        'Waiting Response', 'Waiting Instructions', 'Suspended']:
                        locked = locked + task.points
                    elif task.stage_id.name in ['Done']:
                        used = used + task.points
                elif task.points < 0:
                    if task.stage_id.name in ['Done']:
                            tot = tot - task.points

            free = tot - (used + locked)
            
            record.total_points = tot
            record.used_points = used
            record.locked_points = locked
            record.free_points = free