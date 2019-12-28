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


class Invoice(models.Model):

    _inherit = 'account.invoice'

    # override to reset compute_is_invoiced
    # on crm helpdesk
    @api.multi
    def unlink(self):
        """
            Delete all record(s) from recordset
            return True on success, False otherwise
    
            @return: True on success, False otherwise
        """

        tickets = self.env['crm.helpdesk'].sudo().search(
            [('invoice_id', 'in', self.ids)]
        )
    
        result = super(Invoice, self).unlink()

        # force compute
        # reset invoiced on task
        for t in tickets:
            if t.task_id and t.task_id.invoiced:
                t.task_id.invoiced = False
    
        return result
