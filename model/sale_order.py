# -*- coding: utf-8 -*-
""" override sale order """

import pprint
import logging

from openerp import models, fields, api, exceptions, tools
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """
        override sale order
        1) domain task_to_invoice_ids only if not ticket
    """

    _inherit = 'sale.order'

    # Fields

    task_to_invoice_ids = fields.One2many(
        domain=[('ticket_id', '=', False)]
    )