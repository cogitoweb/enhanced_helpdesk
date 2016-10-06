# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

import logging

from openerp import models,fields, api
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class hd_config_settings(models.TransientModel):
    _name = 'cogito.helpdesk.config.settings'
    _inherit = 'res.config.settings'

    

    
    default_helpdesk_email = fields.Char(
        string='Helpdesk E-mail',
        required=True,
        help="E-mail di servizio",
        default_model='cogito.helpdesk.config.settings',
        translate=True,
    )







