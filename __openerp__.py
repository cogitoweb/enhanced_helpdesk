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
    'version': '0.2',
    'category': 'CRM',
    'description': """
Enhanced Openerp Helpdesk and Ticketing support
""",
    'author': 'Apulia Software Srl',
    'website': 'www.apuliasoftware.it',
    'license': 'AGPL-3',
    "depends": ['base', 'web', 'crm_helpdesk', 'project', 'portal', 'base_cogitoweb'],

    "data": [
        'view/wizard_change_user.xml',
        'view/wizard_merge_ticket.xml',
        
        'view/crm_helpdesk_view.xml',
        'view/crm_case_categ_view.xml',
        'view/wizard_ticket_reply.xml',
        'view/wizard_ticket_cancel.xml',
        
        'view/project_view.xml',
        'view/partner_view.xml',
        'view/company_view.xml',
        #'view/account_invoice_view.xml',
        'view/guide_view.xml',
        'view/helpdesk_status.xml',
        
        'data/ticket_status_data.xml',
        'data/helpdesk_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        
        'workflow/helpdesk_workflow.xml',
        ],
    "update_xml": [],
    "demo_xml": [],
    "active": False,
    "installable": True
}