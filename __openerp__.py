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
    'version': '0.5',
    'category': 'CRM',
    'description': """
Enhanced Openerp Helpdesk and Ticketing support
""",
    'author': 'Apulia Software Srl & Cogito Srl',
    'website': 'www.apuliasoftware.it',
    'license': 'AGPL-3',
    "depends": ['crm_helpdesk', 'portal', 'project_task_projectref_cogitoweb'],

    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',

        'view/wizard_ticket_reply.xml',
        'view/wizard_ticket_reply_user.xml',
        'view/wizard_ticket_cancel.xml',
        'view/wizard_ticket_from_so.xml',
        'view/wizard_ticket_start_work.xml',

        'view/account_analytic_account.xml',
        'view/account_invoice_view.xml',
        'view/company_view.xml',
        'view/crm_helpdesk_view.xml',
        'view/crm_helpdesk_menu.xml',
        'view/crm_case_categ_view.xml',
        'view/product_category.xml',
        'view/project_view.xml',
        'view/partner_view.xml',
        'view/guide_view.xml',
        'view/helpdesk_status.xml',
        'view/hr_contract.xml',
        'view/sales_order_view.xml',
        
        'data/helpdesk_status_data.xml',
        'data/helpdesk_data.xml',
        'data/helpdesk_actions.xml',
        'workflow/helpdesk_workflow.xml',
        
        'view/webclient_templates.xml'
        
        ],
    
    'qweb': [ 
        "static/src/xml/base.xml", 
    ],

    "update_xml": [],
    "demo_xml": [],
    "active": False,
    "application": True,
    "installable": True
}
