# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Apulia (<info@apuliasoftware.it>)
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


from openerp import models, fields, api, SUPERUSER_ID

from openerp.tools.translate import _
from openerp.exceptions import Warning
from openerp import workflow
from dateutil import parser
from datetime import datetime, timedelta

from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qs

import pprint

import logging
_logger = logging.getLogger(__name__)


class CrmHelpdesk(models.Model):

    _inherit = "crm.helpdesk"
    _rec_name = 'display_name'


    # selezione del richiedente
    #
    @api.model
    def _get_request_allowed_ids(self):
        
        request_allowed_ids = []
        
        # se sono un utente esterno
        if self.env.user.has_group('enhanced_helpdesk.ticketing_external_user'):
            request_allowed_ids.append(self.env.user.id)
        else:
            # altrimenti prendo solo quelli che sono esterni
            all_users = self.env['res.users'].search([('active', '=', True)])
            
            for u in all_users:
                if u.has_group('enhanced_helpdesk.ticketing_external_user'):
                    request_allowed_ids.append(u.id)
                
        return [('id', 'in', request_allowed_ids)]
    
    @api.onchange('request_id')
    def on_change_request_id(self):
        
        result = []
        
        current_request_id = self.request_id.id
        current_request_id_partner = self.request_id.partner_id.id
        current_request_id_company = self.request_id.partner_id.parent_id.id

        relationship_recordset = self.env['project.project'].search(
            [
                ('analytic_account_id.partner_id', 'in', (current_request_id_company, current_request_id_partner, current_request_id))
            ]
        )
        lista_project_ids = relationship_recordset.mapped('id')

        if current_request_id_company == 1:
            # il richiedente è un account del main partner, nessun filtro
            result = {
                'domain': {
                    'project_id': [
                        ('state', '=', 'open'),
                        ('privacy_visibility', 'in', ['portal'])
                    ]
                }
            }
        elif lista_project_ids:
            # il richiedente è un account esterno. Restituisce solo id dei progetti collegati
            result = {
                'domain': {
                    'project_id': [
                        ('state', '=', 'open'),
                        ('privacy_visibility', 'in', ['portal']),
                        ('id', 'in', lista_project_ids),
                        ('analytic_account_id.account_type', '=', 'PM')
                    ]
                }
            }
        else:
            # Se non ci sono progetti collegati non permette di selezionare nulla
            result = {
                'domain': {
                    'project_id': [('id', 'in', [0])]
                }
            }

        return result

    def _get_request_user_default(self):
        if self.env.user.has_group('enhanced_helpdesk.ticketing_external_user'):
            return self.env.user
        else:
            users = self.env['res.users'].search(self._get_request_allowed_ids(), order='name asc')

            if(users):
                return users[0]

            ## non e possibile restituire None
            ## restituisco l'utente autenticato
            return self.env.user
    #
    # fine selezione richiedente
    
    def _get_projects_id(self):
        current_request_id = self.request_id.id
        relationship_recordset = self.search([('request_id', '=', current_request_id)])
        lista_project = relationship_recordset.mapped('project_id')
        lista_project_ids = lista_project.mapped('id')

        return lista_project_ids

    def _get_ticket_status_default(self):
        ## default status
        status_code = 'new'
        pool = self.pool.get('helpdesk.ticket.status')
        status_ids = pool.search(self._cr, self._uid, [('status_code','=',status_code)])
        
        if not(status_ids):
            raise Warning(_('No status with wired code %s') % status_code)
            
        return status_ids[0]
    
    def _get_reject_reasons(self):
        return [
                ('wrong_effort', _('Inadequate economic effort')), 
                ('wrong_scheduling', _('Inadequate planning')), 
                ('changed_idea', _('Changed idea, activity is no longer necessary')), 
                ('made_myself', _('I solved my problem by myself')), 
                ('not_compliant', _('The delivery does not match the initial requirements')), 
                ('account_contact', _('I want to be contacted by my account'))
        ]

    @api.depends('task_id.date_deadline')
    def _compute_task_deadline(self):
        for record in self:
            record.task_deadline = record.task_id.date_deadline if record.task_id else False

    @api.depends('project_id.partner_id')
    def _compute_partner_id(self):
        for record in self:
            record.partner_id = record.project_id.partner_id if record.project_id else False

    # ---- Fields
    source = fields.Selection(
        [
            ('portal', 'Portal'),
            ('phone', 'Phone'),
            ('mail', 'Mail'),
            ('internal', 'Internal'),
        ],
        index=True,
        string='Source', default='portal')
       
    request_id = fields.Many2one('res.users',
                                 required=True,
                                 index=True,
                                 string='Sender',
                                 default=_get_request_user_default,
                                 domain=_get_request_allowed_ids)

    external_ticket_url = fields.Char(compute='compute_external_ticket_url')
    helpdesk_qa_ids = fields.One2many('helpdesk.qa', 'helpdesk_id')
    attachment_ids = fields.One2many('ir.attachment',
                                     'crm_helpdesk_id')
    display_name = fields.Char(string='Ticket',
                               compute='compute_display_name',)
    display_id = fields.Char(string='Ticket ID',
                               compute='compute_display_name',)
    merge_ticket_id = fields.Many2one('crm.helpdesk')
    merge_ticket_ids = fields.One2many('crm.helpdesk', 'merge_ticket_id')
    related_ticket = fields.Html()

    project_id = fields.Many2one(
        'project.project', required=True, string='Project',
        index=True
    )
    project_reference_id = fields.Many2one(
        related='task_id.project_ref_id',
        store=True,
        index=True
    )
    partner_id = fields.Many2one(
        compute_sudo=True,
        compute=_compute_partner_id,
        store=True,
        index=True
    )
    task_id = fields.Many2one(
        'project.task',
        required=False,
        string='Task',
        index=True
    )
    task_id_id = fields.Char(
        string='Ticket ID',
        compute='compute_display_name'
    )
    
    task_points = fields.Integer(string='Estimated points', related='task_id.points')
    task_effort = fields.Float(string='Time effort (hours)', related='task_id.planned_hours')
    task_deadline = fields.Date(
        string='Deadline',
        compute_sudo=True,
        compute=_compute_task_deadline,
        store=True,
        index=True
    )

    task_direct_sale_line_id = fields.Many2one(
        related='task_id.direct_sale_line_id',
        store=True,
        index=True
    )
    task_direct_sale_order_id = fields.Many2one(
        related='task_id.sale_order_id',
        store=True,
        index=True
    )
    task_product_id = fields.Many2one(
        related='task_id.product_id',
        store=True,
        index=True
    )

    is_emergency = fields.Boolean(string="Is Emergency", related='categ_id.emergency')
    price = fields.Float(string='Price', compute='compute_ticket_price', store=True)
    cost = fields.Float(string='Cost', related='task_id.cost', readonly=True)

    ticket_status_id = fields.Many2one('helpdesk.ticket.status', default=1,
                                       string="Ticket Status", track_visibility='onchange',
                                       index=True); 
    proxy_status_code = fields.Char(related='ticket_status_id.status_code')
    proxy_user_id = fields.Many2one(
        related='task_id.user_id',
        store=True,
        index=True
    )
    
    reject_reason = fields.Selection(_get_reject_reasons, string='Reject Reason')
    reject_descr = fields.Text('Reject description')
    
    ignore_invoicing = fields.Boolean(
        compute='compute_ignore_invoicing',
        store=True,
        index=True
    )
    invoiced = fields.Boolean(
        compute='compute_is_invoiced',
        store=True,
        index=True
    )
    invoice_id = fields.Many2one(
        related='task_id.invoice_id'
    )
    
    last_answer_user_id = fields.Many2one('res.users', compute='compute_ticket_last_answer', string="Last Answer User")
    
    last_answer_date = fields.Datetime(
        compute='compute_ticket_last_answer',
        string="Last Answer Date",
        store=True,
        index=True)
    
    account_type = fields.Selection(related='project_id.analytic_account_id.account_type')

    _track = {
        'merge_ticket_id': {
            'enhanced_helpdesk.merged':
            lambda self, cr, uid, o, c=None: o['merge_ticket_id'] is not False,
        },
    }
    
    @api.multi
    @api.depends('task_id.an_acc_by_prj.pre_paid', 'task_id.an_acc_by_prj.custom_invoicing_plan')
    def compute_ignore_invoicing(self):

        for r in self:
            r.ignore_invoicing = True if r.task_id.an_acc_by_prj.pre_paid or r.task_id.an_acc_by_prj.custom_invoicing_plan else False

    # update crm_helpdesk set invoiced = case when task_id in (select id from project_task
    # where invoiced or invoice_id is not null) then true else false end;
    @api.multi
    @api.depends('task_id.invoice_id', 'task_id.invoiced')
    def compute_is_invoiced(self):

        for r in self:
            r.invoiced = True if r.task_id.invoice_id or r.task_id.invoiced else False

    @api.multi
    @api.depends('task_id.points', 'task_id.direct_sale_line_id')
    def compute_ticket_price(self):
        
        last_price = 0
        for r in self:
            price = 0

            if r.task_direct_sale_line_id:

                line = r.task_direct_sale_line_id
                r.price = (line.product_uos_qty * line.price_unit) - line.discount

            elif(r.project_id and r.project_id.analytic_account_id):

                r.price = r.task_points * r.project_id.analytic_account_id.point_unit_price

            else:
                r.price = 0

            last_price = r.price

        # return last price to caller
        # for wizard in helpdesk
        return last_price

    @api.multi
    @api.depends('helpdesk_qa_ids')
    def compute_ticket_last_answer(self):
        for t in self:
            user_id = False
            date = False
            # ----- Keep the user from the last answer
            if t.helpdesk_qa_ids:
                answer = t.helpdesk_qa_ids[-1]
                user_id = answer.user_id.id
                date = answer.date
            t.last_answer_user_id = user_id
            t.last_answer_date = date



    @api.one
    @api.depends('name')
    def compute_display_name(self):
        self.display_name = '#%s - %s' % (self.id, self.name)
        self.display_id = '#%s' % (self.id)
        self.task_id_id = '%s' % (self.task_id.id)
        


    @api.multi
    def compute_external_ticket_url(self):
        for ticket in self:
            url = self._get_signup_url(ticket)
            ticket.external_ticket_url = url or ''



    @api.model
    def create(self, values):

        res = super(CrmHelpdesk, self).create(values)
        
        # ----- Create task related with this ticket
        task_value = {
            'project_id': values['project_id'],
            'partner_id': values['partner_id'],
            'name': values['name'],
            'description': values['description'],
            'ticket_id': res.id,
            'product_id': values.get('task_product_id', False),
            'direct_sale_line_id': values.get('task_direct_sale_line_id', False),
            'user_id': values.get('proxy_user_id', False),
            'stage_id': res.ticket_status_id.stage_id.id if res.ticket_status_id.stage_id else 2,
            'date_deadline': values.get('task_deadline', False),
        }

        # - guess product
        if not values.get('task_product_id', False) and not values.get('task_direct_sale_line_id', False):
            aaa = self.env['project.project'].sudo().browse(
                values['project_id']
            ).analytic_account_id

            if aaa and aaa.ticket_product_id:
                task_value['product_id'] = aaa.ticket_product_id.id
        
        # task creation
        task_id = self.env['project.task'].sudo().create(task_value)
        
        # ---- if emergency priority = 2 (hight)
        if(res.is_emergency):
            res.priority = '2'
        
        # ---- register self task
        res.task_id = task_id
        
        before_body = _('Project: %s') % task_id.project_id.name
        before_body += '<br />'
        before_body += _('Category: %s') % res.categ_id.name
        before_body += '<br />'
        before_body += _('Priority: %s') % res.priority
        before_body += '<br /><hr />'
        before_body += _('Description: %s') % res.description
        
        # ---- send mail to support for the new ticket
        self.send_notification_mail(
            template_xml_id='email_template_ticket_new',
            object_class='crm.helpdesk',
            object_id=res.id,
            expande={'before_body': before_body}
            )

        # ---- if proxy_user_id move ticket to assigned
        if values.get('proxy_user_id', False):
            workflow.trg_validate(self._uid, 
                                  'crm.helpdesk', 
                                  res.id, 
                                  'ticket_assigned', self._cr)

        return res

    # override to sync related tasks projects
    @api.multi
    def write(self, values):

        res = super(CrmHelpdesk, self).write(values)

        if not self.env.context.get('skip_sync_projects'):
            if 'project_id' in values:
                for r in self:
                    if r.task_id.project_id.id != values['project_id']:
                        r.task_id.with_context(skip_sync_projects=True).write(
                            {
                                'project_id': values['project_id']
                            }
                        )


        return res

    @api.onchange('request_id')
    def onchange_requestid(self):
        self.user_id = False
        if self.request_id:
            self.partner_id = self.request_id.partner_id.parent_id.id
            self.email_from = self.request_id.email


    @api.onchange('project_id')
    def onchange_projectid(self):

        if self.project_id:
            self.partner_id = self.project_id.partner_id.id


    ## compute direct link to ticket
    ##
    def _get_signup_url(self, ticket):
        user_logged = self.env.user.id
        partner = ticket.request_id.partner_id
        if user_logged == partner.id:
            return False
        action = 'enhanced_helpdesk.action_enhanced_helpdesk'
        ctx = {'signup_force_type_in_url':'login'}
        
        val = partner._get_signup_url_for_action(
            action=action, view_type='form',
            res_id=ticket.id, context=ctx)[partner.id]
        
        ## infamous hack to 
        ## redirect to login instead of signup or reset password
        if(val):
            
            # remove login parameter
            u = urlparse(val)
            query = parse_qs(u.query)
            query.pop('login', None)
            u = u._replace(query=urlencode(query, True))
            # turn to login instead of..
            val = u.geturl().replace('web/signup?', 'web/login?').replace('web/reset_password?', 'web/login?')

        return val

    # change status
    # base on code
    def _change_status(self, status_code):
        
        status_ids = self.env['helpdesk.ticket.status'].search([('status_code','=',status_code)])
        status = status_ids[0] if status_ids else False

        if not(status):
            raise Warning(_('No status with wired code %s') % status_code)

        _logger.info("going to status %s", status)
        
        self.write({'ticket_status_id':status.id}) 
        
        ## update related task status
        if(status.stage_id):
            
            task_stage_id = status.stage_id.id
            
            task = self.task_id

            _logger.info("stage %s" % task_stage_id)

            if task_stage_id in [7]:
                _logger.info("check predecessors")
                for predecessor in task.sudo().predecessor_ids:
                    predecessor.sudo().write({'stage_id': task_stage_id})
                    _logger.info("forced predecessor rel. task %s to stage %s", predecessor.id, task_stage_id)

            task.sudo().write({'stage_id': task_stage_id})
            _logger.info("migrated rel. task %s to stage %s", task.id, task_stage_id)
            
            if task.sudo().child_ids:
                for sub in task.sudo().child_ids:
                    sub.sudo().write({'stage_id': task_stage_id})
                    _logger.info("migrated child task %s to stage %s", sub.id, task_stage_id)

    # send email
    #
    def send_notification_mail(self,
                               template_xml_id=None,
                               object_class=None,
                               object_id=False,
                               expande=None,
                               custom_deliver=None,
                               custom_internal_deliver=None):
        # ---- send mail to support for the new ticket
        company = self.env['res.users'].browse(SUPERUSER_ID).company_id
    
        ## address composition
        ##
        ticket = None
        ticket_reply = None
        if(object_class == "crm.helpdesk"):
            ticket = self.env[object_class].browse(object_id)
        else:
            ticket_reply = self.env[object_class].browse(object_id)
            ticket = ticket_reply.helpdesk_id
        
        #
        # user
        #
        mail_to = ['"%s" <%s>' % (ticket.request_id.name, ticket.request_id.email)]
        mail_to_internal = []
        
        #
        # default company email
        #
        if(company.email_ticket):
            mail_to_internal.extend(['"%s" <%s>' % (company.name, company.email_ticket)])
        
        #
        # PM email
        #
        if(ticket.sudo().task_id.project_id.user_id):
            mail_to_internal.extend(['"%s" <%s>' % (ticket.sudo().task_id.project_id.user_id.name, 
                    ticket.sudo().task_id.project_id.user_id.email)])
            
        # vendite e direzione (solo il primo)
        if(template_xml_id == 'email_template_ticket_new'):

            vendite = self.add_vendite_contact()
            if vendite:
                mail_to_internal.extend(vendite) 

            direzione = self.add_direzione_contact()
            if direzione:
                mail_to_internal.extend(direzione)
        
        #
        # Assigned to task user
        #
        if(ticket.sudo().task_id.user_id):
            mail_to_internal.extend(['"%s" <%s>' % (ticket.sudo().task_id.user_id.name, 
                    ticket.sudo().task_id.user_id.email)])
            
        #
        # Project TEAM emails only for first email
        #
        if(template_xml_id == 'email_template_ticket_new'):
            for member in ticket.sudo().task_id.project_id.members:
                dest = '"%s" <%s>' % (member.name, member.email)
                if((dest in mail_to_internal) == False):
                    mail_to_internal.extend([dest])
            
        #
        # Custom deliver
        #
        if custom_deliver:
            mail_to.extend(custom_deliver)

        #
        # Custom deliver internal
        #
        if custom_internal_deliver:
            mail_to_internal.extend(custom_internal_deliver)

        # ----- Message composition  
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference(
            'enhanced_helpdesk', template_xml_id)[1] or False
        template_model = self.env['email.template']
        template = template_model.sudo().browse(template_id)
        text = template.body_html
        subject = template.subject
        text = template_model.render_template(text, object_class, object_id)
        subject = template_model.render_template(subject, object_class, object_id)
            
        if(ticket.is_emergency):
            subject = '- EMERG - ' + subject
            
        subject = ('[%s Ticketing System] ' % company.name) + subject
        
        # ---- Adding text to mail body
        if expande:
            if expande.get('after_body', False):
                text = '%s %s' % (text, expande['after_body'])
            if expande.get('before_body', False):
                text = '%s %s' % (expande['before_body'], text)
            
        # ----- Create and send mail
        # -----
        mail_model = self.env['mail.mail']
        mail_value = {
            'body_html': text,
            'subject': subject,
            'email_from': company.email_ticket,
            'email_to': ''
            }
        # ----- external
        if(len(mail_to) > 0):
            mail_value['email_to'] = ','.join(mail_to)
            msg_internal = mail_model.sudo().create(mail_value)
            mail_model.sudo().send([msg_internal.id])
        # ----- internal
        if(len(mail_to_internal) > 0):
            mail_value['email_to'] = ','.join(mail_to_internal)
            msg_external = mail_model.sudo().create(mail_value)
            mail_model.sudo().send([msg_external.id])

        # ----- Create a message in thread for log purposes
        if(template_xml_id == 'email_template_ticket_change_state' and expande.get('before_body', False)):
            thread_message_value = {
                'message': expande.get('before_body', False),
                'helpdesk_id': ticket.id,
                'user_id': self._uid,
                }
            reply_id = self.env['helpdesk.qa'].with_context(nomail=True).create(thread_message_value)
        
        return True

    #
    #
    #
    def set_status_email_text(self, prev_status):

        translated_prev_status = _(prev_status)
        translated_new_status = _(self.ticket_status_id.status_name)

        return _('il ticket è passato dallo stato <strong>%s</strong> allo stato <strong>%s</strong><br />') % (
            translated_prev_status, translated_new_status
        )
    
    #
    #  recupero contatti indicati come fatturazione sul partner
    #
    def add_invoice_contacts(self):
    
        # search for notification contact on partner child_ids of type..
        custom_deliver = []
        child_ids = None
        if(self.task_points > 0 and self.project_id.partner_id):
            child_ids = self.sudo().project_id.partner_id.child_ids
        
        if(child_ids):
            for child in child_ids:

                ## right type and not myself
                if(child.type and child.type == 'invoice' and child.id != self.request_id.partner_id.id):
                    custom_deliver.extend(['"%s" <%s>' % (child.name, child.email)])
                    
        return custom_deliver
    
    #
    #  recupero il contatto indicato come direzione
    #
    def add_direzione_contact(self):
    
        # direzione
        mail_to_internal = []
        analytic_direction_id = self.env['ir.config_parameter'].sudo().get_param('internal_analytic_direction_id', default=False)
        if analytic_direction_id:
            aaa = self.env['account.analytic.account'].sudo().browse(int(analytic_direction_id))
            if aaa and aaa.manager_id:
                mail_to_internal.extend(
                    ['"%s" <%s>' % (aaa.manager_id.name, 
                    aaa.manager_id.email)]
                )

        return mail_to_internal

    #
    #  recupero il contatto indicato come vendite
    #
    def add_vendite_contact(self):

        mail_to_internal = []
        analytic_sales_id = self.env['ir.config_parameter'].sudo().get_param('internal_analytic_account_sales_id', default=False)
        if analytic_sales_id:
            aaa = self.env['account.analytic.account'].sudo().browse(int(analytic_sales_id))
            if aaa and aaa.manager_id:
                mail_to_internal.extend(
                    ['"%s" <%s>' % (aaa.manager_id.name, 
                    aaa.manager_id.email)]
                )

        return mail_to_internal

    #
    # WORKFLOW
    #

    @api.multi
    def new_ticket(self):
        _logger.info("call to new_ticket")
    
    @api.multi
    def assigned_ticket(self):
        _logger.info("call to assigned_ticket")
        
        prev_status = self.ticket_status_id.status_name
        self._change_status('ass') 
        
        before_body = self.set_status_email_text(prev_status)
        before_body += _('<br />il ticket è stato assegnato a %s') % self.sudo().task_id.user_id.name
        
        expande = {'before_body': before_body}
        
        self.send_notification_mail(
            'email_template_ticket_change_state', 
            'crm.helpdesk',
            self.id,
            expande
        )

    @api.multi
    def pending_ticket(self):
        _logger.info("call to pending_ticket")
        
        prev_status = self.ticket_status_id.status_name
        self._change_status('app') 
        
        deadline_date = parser.parse(self.task_deadline)
        deadline = deadline_date.strftime('%d/%m/%Y')
        
        before_body = self.set_status_email_text(prev_status)
        before_body += _('<br />il ticket è stato quotato %s punti') % self.task_points
        before_body += _('<br />consegna prevista entro il %s') % deadline
        before_body += _('<br /><br />E\' necessaria la Vs. approvazione della stima per procedere.')
        
        expande = {'before_body': before_body}
        
        self.send_notification_mail(
            'email_template_ticket_change_state', 
            'crm.helpdesk', 
            self.id,
            expande,
            [],
            self.add_direzione_contact()
        )

    @api.multi
    def wait_ticket(self):
        _logger.info("call to wait_ticket")
        
        prev_status = self.ticket_status_id.status_name
        self._change_status('wait')
        
        before_body = self.set_status_email_text(prev_status)
        before_body += _('<br />il ticket è stato sospeso. Il lavoro potrà essere ripreso in un momento successivo.')
        
        expande = {'before_body': before_body}

        self.send_notification_mail(
            'email_template_ticket_change_state', 
            'crm.helpdesk', 
            self.id,
            expande
        )

    @api.multi
    def working_ticket(self):
        _logger.info("call to working_ticket")
        
        # rejected work
        is_rejected = False
        if(self.proxy_status_code == 'dlv'):
            _logger.info("rejected work")
            is_rejected = True
            
        # emergency work
        if(self.is_emergency):
            _logger.info("emergency work")
            
        # standard approved work
        custom_deliver = []
        is_approved = False
        if(self.proxy_status_code == 'app'):
            
            _logger.info("approved estimation")
            is_approved = True
            custom_deliver.extend(self.add_invoice_contacts())

        deadline_date = None
        deadline = None
        if(self.task_deadline):            
        	deadline_date = parser.parse(self.task_deadline)
        	deadline = deadline_date.strftime('%d/%m/%Y')
        
        prev_status = self.ticket_status_id.status_name
        self._change_status('wrk') 
        
        before_body = self.set_status_email_text(prev_status)
        
        if(is_approved):
            before_body += _('<br />è stata approvata la quotazione di %s punti da parte di %s') % (self.task_points,self.env.user.name)
            before_body += _('<br />consegna prevista entro il %s') % deadline
        
        if(is_rejected):
            before_body += _('<br />la consegna è stata rifiutata ed il ticket è ritornato in lavorazione. Verrete contattati da uno dei nostri esperti.')
            
        if(self.is_emergency):
            before_body += _('<br />le fasi di quotazione e approvazione sono state saltate a causa della categoria di intervento in emergenza')
            before_body += _('<br />la calendarizzazione sarà immeditata, l\'effort richiesto sarà comunicato a consuntivo')
        
        expande = {'before_body': before_body}
        
        self.send_notification_mail(
            'email_template_ticket_change_state', 
            'crm.helpdesk', 
            self.id,
            expande,
            custom_deliver
        )

    @api.multi
    def delivered_ticket(self):
        _logger.info("call to delivered_ticket")
        
        prev_status = self.ticket_status_id.status_name
        prev_status_code = self.ticket_status_id.status_code
        self._change_status('dlv') 
        
        before_body = self.set_status_email_text(prev_status)

        ## direct deliver
        if(prev_status_code == 'ass'):
            before_body += _('<br />la segnalazione è stato risolta ed il ticket non necessita di ulteriori interventi,')

        before_body += _('<br />verificare il prodotto e validare la consegna')
        
        expande = {'before_body': before_body}
        
        self.send_notification_mail(
            'email_template_ticket_change_state', 
            'crm.helpdesk',
            self.id,
            expande,
            [],
            self.add_direzione_contact()
        )
        
    @api.multi
    def completed_ticket(self):
        _logger.info("call to completed_ticket")
        
        prev_status = self.ticket_status_id.status_name
        self._change_status('ok') 
        
        before_body = self.set_status_email_text(prev_status)
        before_body += _('<br />la consegna del ticket è stata accettata da %s') % self.env.user.name
        before_body += _('<br />l\'effort richiesto per il ticket è stato di %s punti') % self.task_points

        expande = {'before_body': before_body}
        
        custom_deliver = self.add_invoice_contacts()
        
        self.send_notification_mail(
            'email_template_ticket_change_state', 
            'crm.helpdesk',
            self.id,
            expande,
            custom_deliver
        )

    @api.multi
    def deleted_ticket(self):     
        _logger.info("call to deleted_ticket")
        
        prev_status = self.ticket_status_id.status_name
        self._change_status('xx') 
        
        before_body = self.set_status_email_text(prev_status)
        before_body += _('<br />il ticket è stato annullato da %s') % self.env.user.name

        expande = {'before_body': before_body}
        
        self.send_notification_mail(
            'email_template_ticket_change_state', 
            'crm.helpdesk',
            self.id,
            expande
        )

    @api.multi
    def refuse_ticket(self):
        _logger.info("call to refuse_ticket")
        
        prev_status = self.ticket_status_id.status_name
        self._change_status('xx') 
        
        before_body = self.set_status_email_text(prev_status)
        before_body += _('<br />la quotazione è stata rifiutata ed il ticket è stato annullato')

        expande = {'before_body': before_body}
        
        self.send_notification_mail(
            'email_template_ticket_change_state', 
            'crm.helpdesk',
            self.id,
            expande
        )

    #
    # scheduled action
    #
    @api.model
    def completed_expired_ticket_batch(self):
        _logger.info("call to expired ticket")

        days = 15
        records = self.env['crm.helpdesk'].search([
            ('proxy_status_code', '=', 'dlv'),
            ('last_answer_date', '<', (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:$S'))
        ])

        _logger.info("try to complete %s tickets" % days)

        for r in records:

            prev_status = r.ticket_status_id.status_name
            r._change_status('ok')

            before_body = r.set_status_email_text(prev_status)
            before_body += _('<br />la consegna del ticket è stata accettata in via automatica per decorrenza dei termini di approvazione (%s giorni)') % days
            before_body += _('<br />l\'effort richiesto per il ticket è stato di %s punti') % r.task_points

            expande = {'before_body': before_body}

            custom_deliver = r.add_invoice_contacts()

            self.send_notification_mail('email_template_ticket_change_state',
                                        'crm.helpdesk', r.id, expande, custom_deliver)

    #
    # FATTURAZIONE
    #
    @api.multi
    def invoice_ticket(self):

        # costanti
        ACCOUNT_ID = 33
        PRODUCT_ACCOUNT_ID = 5342
        JOURNAL_ID = 1

        # counters
        invoice_count = 0
        ticket_zero_count = 0
        ticket_count = 0

        # start check
        for record in self:

            # check prodotto
            if not record.task_product_id:

                raise Warning(
                    _("Ticket %s does not have sale product") % record.id
                )

            # check stato
            if record.proxy_status_code not in ['ok']:

                raise Warning(
                    _("Ticket %s has wrong status") % record.id
                )

            # check ignore_invoicing
            if record.ignore_invoicing:

                raise Warning(
                    _("Ticket %s has to be ignored in invoicing procedure") % record.id
                )

            # check invoiced
            if record.invoiced:

                raise Warning(
                    _("Ticket %s has been already invoiced") % record.id
                )
        # end check     

        # ordino recordset
        records = self.search(
            [('id', 'in', self.ids)],
            order="partner_id asc, task_direct_sale_order_id asc, task_product_id asc, id asc"
        )

        invoice = False
        sale_offer_id = False
        invoice_line = False
        invoice_line_zero = False
        for record in records:

            taxes = []
            for t in record.task_product_id.taxes_id:
                taxes.append((4, t.id))

            # se cambia offerta fai reset
            if record.task_direct_sale_line_id:
                if sale_offer_id != record.task_direct_sale_line_id.order_id.id:
                    invoice = False

                sale_offer_id = record.task_direct_sale_line_id.order_id.id

            # testata

            if not invoice or invoice.partner_id.id != record.partner_id.id:

                invoice = self.env['account.invoice'].create(
                    {
                        'partner_id': record.partner_id.id,
                        'account_id': record.partner_id.property_account_receivable.id if \
                            record.partner_id.property_account_receivable else ACCOUNT_ID,
                        'journal_id': JOURNAL_ID,
                        'fiscal_position': record.partner_id.property_account_position.id if \
                            record.partner_id.property_account_position else False,
                        'order_reference_id': sale_offer_id,
                        'origin': record.task_direct_sale_line_id.order_id.name if \
                            record.task_direct_sale_line_id else False
                    }
                )

                invoice_line = False
                invoice_line_zero = False
                invoice_count += 1
                _logger.info("created invoice %s for partner %s" % (invoice.id, invoice.partner_id.id))

            # da offerta
            if record.task_direct_sale_line_id:

                invoice_line_from_offer = self.env['account.invoice.line'].create(
                    {
                        'product_id': record.task_product_id.id,
                        'account_id': record.task_product_id.property_account_income.id if \
                            record.task_product_id.property_account_income else PRODUCT_ACCOUNT_ID,
                        'invoice_id': invoice.id,
                        'uos_id': record.task_product_id.uom_id.id,
                        'invoice_line_tax_id': taxes,
                        'price_unit': record.price,
                        'quantity': 1,
                        'name': record.name,
                        'account_analytic_id': record.project_id.analytic_account_id.id
                    }
                )

            # righe a zero
            elif not record.task_points:

                if not invoice_line_zero or record.task_product_id.id != invoice_line_zero.product_id.id:

                    invoice_line_zero = self.env['account.invoice.line'].create(
                        {
                            'product_id': record.task_product_id.id,
                            'account_id': record.task_product_id.property_account_income.id if \
                                record.task_product_id.property_account_income else PRODUCT_ACCOUNT_ID,
                            'invoice_id': invoice.id,
                            'uos_id': record.task_product_id.uom_id.id,
                            'invoice_line_tax_id': taxes,
                            'price_unit': record.project_id.analytic_account_id.point_unit_price,
                            'quantity': 0,
                            'name': 'Ticket a zero punti #%s' % record.id,
                            'account_analytic_id': record.project_id.analytic_account_id.id
                        }
                    )
                else:
                    invoice_line_zero.write(
                        {
                            'name': "%s, #%s" % (invoice_line_zero.name, record.id)
                        }
                    )
                ticket_zero_count += 1
                _logger.info("registered invoice_line_zero %s" % invoice_line_zero.id)

            else:

                # righe con punti
                if not invoice_line or record.task_product_id.id != invoice_line.product_id.id:

                    invoice_line = self.env['account.invoice.line'].create(
                        {
                            'product_id': record.task_product_id.id,
                            'account_id': record.task_product_id.property_account_income.id if \
                                record.task_product_id.property_account_income else PRODUCT_ACCOUNT_ID,
                            'invoice_id': invoice.id,
                            'uos_id': record.task_product_id.uom_id.id,
                            'invoice_line_tax_id': taxes,
                            'price_unit': record.project_id.analytic_account_id.point_unit_price,
                            'quantity': record.task_points,
                            'name': 'Ticket #%s' % record.id,
                            'account_analytic_id': record.project_id.analytic_account_id.id
                        }
                    )
                else:
                    invoice_line.write(
                        {
                            'quantity': invoice_line.quantity + record.task_points,
                            'name': "%s, #%s" % (invoice_line.name, record.id)
                        }
                    )
                ticket_count += 1
                _logger.info("registered invoice_line %s" % invoice_line.id)

            # update back with generated invoice
            invoice.button_reset_taxes()
            record.invoice_id = invoice
        # end loop

        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Ticket invoicing'),
            'message': _(
                "Invoicing procedure completed:\n\n"
                "Generated %s invoices\n\n"
                "%s evaluated tickets\n\n"
                "%s zero points tickets"
            ) % (invoice_count, ticket_count, ticket_zero_count),
        }
    # end method
