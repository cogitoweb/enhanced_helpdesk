# -*- coding: utf-8 -*-
from openerp import fields, models, api, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    # Fields

    ticket_product_id = fields.Many2one(
        string='Product used in tickets',
        comodel_name='product.product',
    )
