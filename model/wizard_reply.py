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

    _name = "wizard.ticket.reply"



    def _get_quote_mode(self):
        
        if(self.env.user.has_group('enhanced_helpdesk.ticketing_support')):
            return 'POINTS'
        elif(self.env.user.has_group('enhanced_helpdesk.ticketing_supplier_support')):
            return 'EFFORT'
        else:
            return 'NONE'
    


    def _get_request_user_default(self):
        
        if(self.task_user_id):
            return self.task_user_id
        
        return self.env.user



    @api.depends('ticket_id')
    def _get_deadline(self):
        
        if(self.ticket_id):
            return self.ticket_id.task_id.date_deadline
        
        return False



    def is_multiple_of(self, num, step=25):
        # (2,30 * 100) mod 25 --> false
        # (2,50 * 100) mod 25 --> true
        return ((num*100) % step) == 0
    


    def _calculate_points_from_effort(self):
        
        # supplier effort instead of points
        if self.effort and self.task_user_id.has_group('enhanced_helpdesk.ticketing_supplier_support'):
            
            # default 6 point * hour
            default_multiplier = 6
            
            #search active contract for user employee
            self._cr.execute("""SELECT coalesce(points_per_hour,0) FROM hr_contract hrc
                        INNER JOIN hr_employee hre ON hre.id = hrc.employee_id
                        INNER JOIN resource_resource rr ON rr.id = hre.resource_id AND rr.active = true 
                        INNER JOIN res_users u ON u.id = rr.user_id 
                        WHERE hrc.date_start <= now() AND coalesce(hrc.date_end, now()) >= now() AND u.id = %s 
                        ORDER BY hrc.id LIMIT 1""" % self.task_user_id.id)
            r = self._cr.fetchone()
            # default is 6 points per hour
            default_multiplier = float(r[0]) if (r and r[0]) else default_multiplier
            
            self.points = math.ceil(self.effort * default_multiplier)

    # ---- Fields
    ticket_id = fields.Many2one('crm.helpdesk')
    ticket_status_id = fields.Many2one('helpdesk.ticket.status', related='ticket_id.ticket_status_id',readonly=True)  
    ticket_reply = fields.Text('Reply')
    attachment = fields.Binary('Attachment')
    attachment_name = fields.Char(size=64)
    proxy_status_code = fields.Char(related='ticket_status_id.status_code')
    proxy_categ_emerg = fields.Boolean(related='ticket_id.is_emergency')
    task_id = fields.Many2one('project.task', related='ticket_id.task_id',readonly=True)
    task_product_id = fields.Many2one(
        related='ticket_id.task_id.product_id'
    )
    task_direct_sale_line_id = fields.Many2one(
        related='ticket_id.task_id.direct_sale_line_id'
    )
    points = fields.Integer(string='Points', related='ticket_id.task_id.points')
    price = fields.Float(string='Price', related='ticket_id.price')
    price_preview = fields.Float(
        readonly=True
    )
    cost = fields.Float(string='Cost', related='ticket_id.task_id.cost')
    effort = fields.Float(string='Time effort (hours)', related='ticket_id.task_id.planned_hours')
    task_user_id = fields.Many2one('res.users',
                                 required=True,
                                 string='Assigned to', 
                                 default=_get_request_user_default,
                                 related='task_id.user_id') 
    deadline = fields.Date(string='Deadline', related='ticket_id.task_id.date_deadline')
    new_deadline = fields.Date()
            
    can_quote_ticket = fields.Boolean(compute='compute_can_quote_ticket')
    quote_mode = fields.Char(default=_get_quote_mode)

    @api.onchange('points', 'task_direct_sale_line_id')
    def onchange_points(self):
        self.price_preview = self.ticket_id.compute_ticket_price()

        return {'value':{
                            'price_preview': self.price_preview
                    }}
    
    @api.multi
    @api.depends('proxy_categ_emerg','proxy_status_code')
    def compute_can_quote_ticket(self):
        
        for r in self:
            if(r.proxy_status_code == 'ass' or (r.proxy_categ_emerg and r.proxy_status_code == 'wrk')):
                r.can_quote_ticket = True
            else:
                r.can_quote_ticket = False

    @api.multi
    def reply(self, context=None, wkf_trigger=''):

        reply_id = False
        if self.ticket_reply or self.new_deadline:

            if(self.new_deadline):

                new_deadline = parser.parse(self.new_deadline).strftime('%d/%m/%Y')
                deadline = self.deadline
                if deadline:
                    deadline = parser.parse(deadline).strftime('%d/%m/%Y')

                    message = (_('La data di consegna del ticket è stata modificata dal %s al %s con la seguente motivazione: %s')
                    % (deadline, new_deadline, self.ticket_reply))
                else:
                    message = (_('La data di consegna del ticket è stata modificata in %s con la seguente motivazione: %s')
                    % (new_deadline, self.ticket_reply))

                self.deadline = self.new_deadline
            else:
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

        # ---- write new value on ticket
        if not self.ticket_id.user_id:
            self.ticket_id.user_id = self._uid
            
        _logger.info('try validate workflow %s', wkf_trigger)
            
        # ---- set new state to ticket
        if wkf_trigger:
            workflow.trg_validate(self._uid, 
                                  'crm.helpdesk', 
                                  self.ticket_id.id, 
                                  wkf_trigger, self._cr)

        return {'type': 'ir.actions.act_window_close'}



    @api.multi
    def ticket_assigned(self):
        return self.reply(wkf_trigger='ticket_assigned')


    
    @api.multi
    def ticket_pending(self):
        
        _logger.info('try pending with deadline %s', self.deadline)
        
        # validation deadline
        if not self.deadline:
            raise Warning(
                    _('Deadline date is mandatory'))

        # validation time
        if not self.is_multiple_of(self.effort, 25):
            raise Warning(
                    _('The time effort must be rounded to 1/4 of an hour and expressed in decimal (1h 30m = 1,50)'))
            
        self._calculate_points_from_effort()

        return self.reply(wkf_trigger='ticket_quoted')



    @api.multi
    def ticket_working(self):
        return self.reply(wkf_trigger='ticket_approved')



    @api.multi
    def ticket_emerg(self):
        return self.reply(wkf_trigger='ticket_emerg')



    @api.multi
    def ticket_delivered(self):
        
        self._calculate_points_from_effort()
        
        # in case of emergency set deadline on delivery date
        if not self.deadline:
            self.deadline = fields.Date.today()
        
        return self.reply(wkf_trigger='ticket_delivered')



    @api.multi
    def ticket_completed(self):
        return self.reply(wkf_trigger='ticket_completed')
