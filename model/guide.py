# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 201 Apulia (<info@apuliasoftware.it>)
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


class CrmHelpdeskGuide(models.Model):

    _name = "crm.helpdesk.guide"
    _order = "title asc"

    # ---- Fields
    title = fields.Char(required=True)
    description = fields.Text(required=True)
    url = fields.Char(required=False)
    file = fields.Binary(required=True)
    filename = fields.Char()
    state = fields.Selection(
        [('draft', 'Draft'), ('need_review', 'Need Review'),
         ('published', 'Published')], default='draft', readonly=False)
    group = fields.Many2one('res.groups')

    @api.multi
    def open_url(self):
        return {'type': 'ir.actions.act_url', 'url': self.url, 'target': 'new'}

    @api.multi
    def set_draft(self):
        self.state = 'draft'
    @api.multi
    def set_need_review(self):
        self.state = 'need_review'
    @api.multi
    def set_published(self):
        self.state = 'published'