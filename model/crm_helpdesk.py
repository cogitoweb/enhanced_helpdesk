# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Apulia (<info@apuliasoftware.it>)
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


class CrmHelpdesk(models.Model):

    _inherit = "crm.helpdesk"

    request_id = fields.Many2one('res.users',
                                 required=True,
                                 string='Richiedente',
                                 default=lambda self: self.env.user)

    _track = {
        'state': {
            'enhanced_helpdesk.open': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'open',
            'enhanced_helpdesk.pending': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'pending',
            'enhanced_helpdesk.done': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'done',
            'enhanced_helpdesk.cancel': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'cancel',
        },
    }

    @api.onchange('request_id')
    def onchange_requestid(self):
        self.user_id = False
        if self.request_id:
            self.partner_id = self.request_id.partner_id.parent_id.id
            mail = self.request_id.email
            self.email_from = mail

    @api.model
    def create(self, values):
        res = super(CrmHelpdesk, self).create(values)
        task_value = {
            'partner_id': values['partner_id'],
            'name': values['name'],
            'description': values['description'],
            'ticket_id': res.id,
            }
        self.env['project.task'].sudo().create(task_value)
        return res
