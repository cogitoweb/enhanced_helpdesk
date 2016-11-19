# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Andre@ (<info@apuliasoftware.it>)
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


from openerp import models, fields, api, SUPERUSER_ID, _
from openerp.exceptions import Warning


class HelpdeskQA(models.Model):

    _name = 'helpdesk.qa'

    # ---- Fields
    message = fields.Text('Message')
    helpdesk_id = fields.Many2one('crm.helpdesk')
    date = fields.Datetime(string='Message Date', default=lambda self: fields.Datetime.now())
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    complete_message = fields.Text(compute='_complete_message')
    attachment_ids = fields.One2many('ir.attachment',
                                     'helpdesk_qa_id')

    @api.multi
    def _complete_message(self):
        for msg in self:
            info = '<img height="40px" \
src="/web/binary/image?model=res.partner&id=%s&field=image_medium" \
/> %s - %s<br /><br />' % (msg.user_id.partner_id.id, msg.user_id.name, msg.date)
            info = '%s%s' % (info, msg.message)
            if len(msg.attachment_ids) > 0:
                info = '%s\n\n%s Attachment(s)' % (info,
                                                   len(msg.attachment_ids))
            msg.complete_message = info

    @api.onchange('message')
    def onchange_message(self):
        if self.message:
            self.complete_message = 'Message Preview\n\n%s' % (self.message)

    @api.multi
    def unlink(self):
        for qa in self:
            # ----- Impossible to delete other user's messages
            if qa.user_id.id != self.env.user.id:
                raise Warning(
                    _('Can not delete messages posted from other users'))
            # ----- Impossibile to delete messages with an answer
            if qa.search([('helpdesk_id', '=', qa.helpdesk_id.id),
                          ('id', '>', qa.id)]):
                raise Warning(
                    _('Can not delete messages with an answer'))
        return super(HelpdeskQA, self).unlink()

    @api.model
    def create(self, values):
        res = super(HelpdeskQA, self).create(values)
#       
        return res
