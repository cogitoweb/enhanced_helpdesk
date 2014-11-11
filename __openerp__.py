# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Apulia Software S.r.l. (<info@apuliasoftware.it>)
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

{
    'name': "Enhanced Helpdesk",
    'version': '0.1',
    'category': 'CRM',
    'description': """
Enhanced Openerp Helpdesk and Ticketing support


External depends:

    * Python Beautiful Soup
""",
    'author': 'Apulia Software Srl',
    'website': 'www.apuliasoftware.it',
    'license': 'AGPL-3',
    "depends": ['base', 'web', 'crm_helpdesk', 'project'],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/helpdesk_data.xml',
        'view/crm_helpdesk_view.xml',
        'view/wizard_ticket_reply.xml',
        'view/project_view.xml',
        'view/partner_view.xml',
        'view/company_view.xml',
        'workflow/helpdesk_workflow.xml',
        ],
    "update_xml": [],
    "demo_xml": [],
    "active": False,
    "installable": True
}
