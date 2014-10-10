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


    def ticket_reply(self):
        import pdb; pdb.set_trace()
        res = self.env['ir.actions.act_window'].for_xml_id(
            self._cr, self._uid, 'enhanced_helpdesk', 'action_ticket_reply',
            self._context)
        return res
