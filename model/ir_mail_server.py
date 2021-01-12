# -*- coding: utf-8 -*-

from openerp import models, fields, api, SUPERUSER_ID, _


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    # fields declaration

    # override field to increase size
    smtp_pass = fields.Char(
        size=69
    )
