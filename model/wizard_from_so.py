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

from openerp import models, fields, api, _
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

    order_id = fields.Many2one('sale.order', string='Order', required=True)
    task_user_id = fields.Many2one('res.users',
                                 string='Assigned to', 
                                 default=_get_request_user_default) 
    deadline = fields.Date(string='Deadline')

    # ----- Methods    

    @api.multi
    def generate(self):

        self.ensure_one()

        self.ticket_generate(False)

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def generate_and_complete(self):

        self.ensure_one()

        if not self.task_user_id or not self.deadline:
            raise Warning(_('Set assignee and deadline to complete tickets'))

        self.ticket_generate(True)

        return {'type': 'ir.actions.act_window_close'}

    def ticket_generate(self, complete):

        # [TODO] TICKET CREATION if not created
        # richiedente account cogito

        tickets = []

        internal_user_id = self.env['ir.config_parameter'].sudo().get_param(
            'internal_user_id', default=False
        )
        
        if not internal_user_id:
            raise Warning(_('Please set internal_user_id param'))

        # crea parametro internal_user_id
        richiedente = self.env['res.users'].browse(
            internal_user_id
        )

        if not richiedente:
            raise Warning(_('Please set VALID internal_user_id param'))

        if not self.order_id.real_project_id:
            raise Warning(_('Please assign project to create tickets'))

        for line in self.order_id.order_line:

            if not line.tasks_ids:

                new_ticket = self.env['crm.helpdesk'].create(
                    {
                        'project_id': self.order_id.real_project_id.id,
                        'partner_id': richiedente.id,
                        'name': line.name,
                        'description': line.name,
                        'task_direct_sale_line_id': line.id,
                        'proxy_user_id': self.task_user_id.id if self.task_user_id else False,
                        'task_deadline': self.deadline,
                        'source': 'internal',
                        'categ_id': self.env.ref('enhanced_helpdesk.crm_case_categ_from_offer').id,
                        'date': fields.Datetime.now()
                    }
                )
                tickets.append(new_ticket)

        if not tickets:
            raise Warning(_('Sorry: there are no tickets to create'))

        # check
        if complete:
            for t in tickets:
                workflow.trg_validate(
                    self._uid, 
                    'crm.helpdesk', 
                    t.id, 
                    'ticket_completed',
                    self._cr
                )

                _logger.info("try to complete id %s" % t.id)

        return True
