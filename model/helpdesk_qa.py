# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Andre@ (<a.gallina@cgsoftware.it>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/Start Date Locatedor modify
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
from BeautifulSoup import BeautifulSoup


class IrAttachment(models.Model):

    _inherit = 'ir.attachment'

    helpdesk_qa_id = fields.Many2one('helpdesk.qa')


class HelpdeskQA(models.Model):

    _name = 'helpdesk.qa'

    # ---- Fields
    message = fields.Text('Message')
    helpdesk_id = fields.Many2one('crm.helpdesk')
    date = fields.Datetime(string='Message Date', default=fields.Date.today())
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    complete_message = fields.Text(compute='_complete_message')
    attachment_ids = fields.One2many('ir.attachment',
                                     'helpdesk_qa_id')

    @api.multi
    def _complete_message(self):
        for msg in self:
            info = '%s - %s\n\n' % (msg.user_id.name, msg.date)
            info = '%s%s' % (info, msg.message)
            if len(msg.attachment_ids) > 0:
                info = '%s\n\n%s Attachment(s)' % (info,
                                                   len(msg.attachment_ids))
            if msg.user_id.signature:
                signature = msg.user_id.signature.replace('<br>', '\n')
                signature = BeautifulSoup(signature)
                info = '%s\n\n---\n%s' % (info, str(signature.text))
            msg.complete_message = info
