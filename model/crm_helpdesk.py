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

#Import logger
import logging
#Get the logger
_logger = logging.getLogger(__name__)


class CrmHelpdesk(models.Model):

    _inherit = "crm.helpdesk"
    _rec_name = 'display_name'



    # Functiont to populate fields.Select()
    # with ticket status coming from database
    @api.model
    def _get_ticket_status(self):
        lst=[]
        for status in self.env['helpdesk.ticket.status'].search([]):
            lst.append((status.id, status.status_name))
        return lst 

    # selezione del richiedente
    #
    @api.model
    def _get_request_allowed_ids(self):
        
        request_allowed_ids = []
        
        _logger.info("_get_request_allowed_ids")
        
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
    
    def _get_request_user_default(self):
        if self.env.user.has_group('enhanced_helpdesk.ticketing_external_user'):
            return self.env.user
        else:
            # non e possibile restituire None
            return self.env.user
    #
    # fine selezione richiedente
    
    # ---- Fields
    source = fields.Selection(
        [('portal', 'Portal'), ('phone', 'Phone'), ('mail', 'Mail')],
        string='Source', default='portal')
       
        
    request_id = fields.Many2one('res.users',
                                 required=True,
                                 string='Richiedente',
                                 default=_get_request_user_default,
                                 domain=_get_request_allowed_ids)

    external_ticket_url = fields.Char(compute='_get_external_ticket_url')
    helpdesk_qa_ids = fields.One2many('helpdesk.qa', 'helpdesk_id')
    attachment_ids = fields.One2many('ir.attachment',
                                     'crm_helpdesk_id')
    display_name = fields.Char(string='Ticket',
                               compute='_compute_display_name',)
    display_id = fields.Char(string='Ticket ID',
                               compute='_compute_display_name',)
    merge_ticket_id = fields.Many2one('crm.helpdesk')
    merge_ticket_ids = fields.One2many('crm.helpdesk', 'merge_ticket_id')
    related_ticket = fields.Html()

    project_id = fields.Many2one('project.project', required=True, string='Progetto')
    task_id = fields.Many2one('project.task', required=False, string='Task')
    
    task_points = fields.Integer(string='Punti stimati', related='task_id.points')
    task_deadline = fields.Date(string='Deadline', related='task_id.date_deadline')


    ticket_status_id = fields.Many2one('helpdesk.ticket.status', default=1 ,string="Ticket Status", track_visibility='onchange'); 
    proxy_status_code = fields.Char(related='ticket_status_id.status_code')
    

    _track = {
        'merge_ticket_id': {
            'enhanced_helpdesk.merged':
            lambda self, cr, uid, o, c=None: o['merge_ticket_id'] is not False,
        },
    }

    @api.one
    @api.depends('name')
    def _compute_display_name(self):
        self.display_name = '#%s - %s' % (self.id, self.name)
        self.display_id = '#%s' % (self.id)

    @api.multi
    def _get_external_ticket_url(self):
        for ticket in self:
            url = self._get_signup_url(ticket)
            self.external_ticket_url = url or ''

    @api.model
    def create(self, values):
        res = super(CrmHelpdesk, self).create(values)
        
        # ----- Create task related with this ticket
        task_value = {
            'project_id': values['project_id'],
            'partner_id': values['partner_id'],
            'user_id': "",
            'name': values['name'],
            'description': values['description'],
            'ticket_id': res.id,
            }
        
        task_id = self.env['project.task'].sudo().create(task_value)
        
        # ---- register self task
        res.task_id = task_id
        
        # ---- send mail to support for the new ticket
        self.send_notification_mail(
            template_xml_id='email_template_ticket_new',
            object_class='crm.helpdesk',
            object_id=res.id,
            expande={'after_body': res.description}
            )

        return res

    @api.onchange('request_id')
    def onchange_requestid(self):
        self.user_id = False
        if self.request_id:
            self.partner_id = self.request_id.partner_id.parent_id.id
            self.email_from = self.request_id.email

    def _get_signup_url(self, ticket):
        user_logged = self.env.user.id
        partner = ticket.request_id.partner_id
        if user_logged == partner.id:
            return False
        action = 'enhanced_helpdesk.action_enhanced_helpdesk'
        partner.signup_prepare()
        val = partner._get_signup_url_for_action(
            action=action, view_type='form',
            res_id=ticket.id)[partner.id]
        return val
            
    # change status
    # base on code
    def _change_status(self, status_code):
        
        pool = self.pool.get('helpdesk.ticket.status')
        status_ids = pool.search(self._cr, self._uid, [('status_code','=',status_code)])
        
        if not(status_ids):
            raise Warning(_('No status with wired code %s') % status_code)
            
        _logger.info("going to status %s", status_ids[0])
        
        self.write({'ticket_status_id':status_ids[0]}) 
        
        ## update related task status
        if(status_code in ('ok', 'xx')):
            
            state_name = 'Done' if(status_code == 'ok') else 'Cancelled'
            stage_pool = self.pool.get('project.task.type')
            stage_ids = stage_pool.search(self._cr, SUPERUSER_ID, [('name','=',state_name)])
            
            if not(status_ids):
                raise Warning(_('No task stage with wired name %s') % state_name)
            
            task = self.task_id
            task.sudo().write({'stage_id': stage_ids[0]})
            _logger.info("migrated rel. task %s to stage %s", task.id, stage_ids[0])
            
            if task.sudo().child_ids:
                for sub in task.sudo().child_ids:
                    sub.sudo().write({'stage_id': stage_ids[0]})
                    _logger.info("migrated child task %s to stage %s", sub.id, stage_ids[0])

        
    # send email
    #
    def send_notification_mail(self, template_xml_id=None,
                               object_class=None, object_id=False,
                               expande=None):
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
        
        # reuested user
        #
        mail_to = ['"%s" <%s>' % (ticket.request_id.name, ticket.request_id.email)]
        # default email
        #
        mail_to.extend(['"%s" <%s>' % (company.name, company.email_ticket)])
        # PM email
        #
        if(ticket.sudo().task_id.project_id.user_id):
            mail_to.extend(['"%s" <%s>' % (ticket.sudo().task_id.project_id.user_id.name, 
                    ticket.sudo().task_id.project_id.user_id.email)])

        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference(
            'enhanced_helpdesk', template_xml_id)[1] or False
        template_model = self.env['email.template']
        template = template_model.sudo().browse(template_id)
        text = template.body_html
        subject = template.subject
        text = template_model.render_template(text, object_class, object_id)
        subject = template_model.render_template(subject, object_class, object_id)
        
        # ---- Adding text to mail body
        if expande and expande.get('after_body', False):
            text = '%s\n\n -- %s' % (text, expande['after_body'])
        
        # ----- Create and send mail
        mail_value = {
            'body_html': text,
            'subject': subject,
            'email_from': company.email_ticket,
            'email_to': mail_to
            }
        mail_model = self.env['mail.mail']
        msg = mail_model.sudo().create(mail_value)
        mail_model.sudo().send([msg.id])
        return msg.id

    
    
    @api.multi
    def new_ticket(self):
        _logger.info("call to new_ticket")
        
        self.send_notification_mail
    
    @api.multi
    def assigned_ticket(self):
        _logger.info("call to assigned_ticket")
        
        self._change_status('ass') 

    @api.multi
    def pending_ticket(self):
        _logger.info("call to pending_ticket")
        
        self._change_status('app') 
        
    @api.multi
    def working_ticket(self):
        _logger.info("call to working_ticket")
        
        if(self.proxy_status_code == 'dlv'):
            # rejected work
             _logger.info("rejected work")
        
        self._change_status('wrk') 
        
    @api.multi
    def delivered_ticket(self):
        _logger.info("call to delivered_ticket")
        
        self._change_status('dlv') 
        
    @api.multi
    def completed_ticket(self):
        _logger.info("call to completed_ticket")
        
        self._change_status('ok') 

    @api.multi
    def deleted_ticket(self):     
        _logger.info("call to deleted_ticket")
        
        self._change_status('xx') 
        
#        self.send_notification_mail(
#            template_xml_id='email_template_ticket_new',
#            object_class='crm.helpdesk',
#            object_id=self.id,
#            expande={'after_body': 'task annullato'}
#            )
            
    @api.multi
    def refuse_ticket(self):
        _logger.info("call to refuse_ticket")
        
        self._change_status('xx') 
              
#        self.send_notification_mail(
#            template_xml_id='email_template_ticket_new',
#            object_class='crm.helpdesk',
#            object_id=self.id,
#            expande={'after_body': 'stima rifiutata'}
#            )

