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


class Partner(models.Model):

    _inherit = 'res.partner'

    ticket_count = fields.Integer(compute='_ticket_count')

    @api.multi
    def _ticket_count(self):
        ticket = self.env['crm.helpdesk']
        for partner in self:
            partner.ticket_count = ticket.search_count(
                [('partner_id', '=', partner.id),
                 ('state', 'not in', ('done', 'cancel')),])
