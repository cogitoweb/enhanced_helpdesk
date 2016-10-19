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

        'ticket_status_id':{
            'enhanced_helpdesk.new':
            lambda self, cr, uid, obj, ctx=None: obj['ticket_status_id'] == '1', 
            'enhanced_helpdesk.assigned':
            lambda self, cr, uid, obj, ctx=None: obj['ticket_status_id'] == '2',
            'enhanced_helpdesk.pending':
            lambda self, cr, uid, obj, ctx=None: obj['ticket_status_id'] == '3',
            'enhanced_helpdesk.working':
            lambda self, cr, uid, obj, ctx=None: obj['ticket_status_id'] == '4', 
            'enhanced_helpdesk.delivered':
            lambda self, cr, uid, obj, ctx=None: obj['ticket_status_id'] == '5',  
            'enhanced_helpdesk.completed':
            lambda self, cr, uid, obj, ctx=None: obj['ticket_status_id'] == '6',
            'enhanced_helpdesk.deleted':
            lambda self, cr, uid, obj, ctx=None: obj['ticket_status_id'] == '7',   
        },
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
            url = self.get_signup_url(ticket)
            self.external_ticket_url = url or ''

    def get_signup_url(self, ticket):
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

    @api.onchange('request_id')
    def onchange_requestid(self):
        self.user_id = False
        if self.request_id:
            self.partner_id = self.request_id.partner_id.parent_id.id
            self.email_from = self.request_id.email

    def send_notification_mail(self, template_xml_id=None,
                               object_class=None, object_id=False,
                               expande=None):
        # ---- send mail to support for the new ticket
        company = self.env['res.users'].browse(SUPERUSER_ID).company_id
        mail_to = ['"%s" <%s>' % (company.name, company.email_ticket)]
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference(
            'enhanced_helpdesk', template_xml_id)[1] or False
        template_model = self.env['email.template']
        template = template_model.sudo().browse(template_id)
        text = template.body_html
        subject = template.subject
        text = template_model.render_template(text, object_class, object_id)
        subject = template_model.render_template(subject, object_class,
                                                 object_id)
        # ---- Get active smtp server
        mail_server = self.env['ir.mail_server'].sudo().search(
            [], limit=1, order='sequence')
        # ---- Adding text to mail body
        if expande and expande.get('after_body', False):
            text = '%s\n\n -- %s' % (text, expande['after_body'])
        # ----- Create and send mail
        mail_value = {
            'body_html': text,
            'subject': subject,
            'email_from': company.email_ticket,
            'email_to': mail_to,
            'mail_server_id': mail_server.id,
            }
        mail_model = self.env['mail.mail']
        msg = mail_model.sudo().create(mail_value)
        mail_model.sudo().send([msg.id])
        return msg.id

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
    
    
    @api.multi
    def new_ticket(self):
        _logger.info("call to new")
        #self.write({'ticket_status_id':1}) 
    
    @api.multi
    def assigned_ticket(self):
        _logger.info("call to assigned")
        #self.write({'ticket_status_id':2}) 

    @api.multi
    def pending_ticket(self):
        _logger.info("call to pending")
        #self.write({'ticket_status_id':2}) 
        
    @api.multi
    def working_ticket(self):
        _logger.info("call to working")
        #self.write({'ticket_status_id': 4})
        
    @api.multi
    def delivered_ticket(self):
        _logger.info("call to deli")
        #self.write({'ticket_status_id': 4})
        
    @api.multi
    def completed_ticket(self):
        _logger.info("call to comp")
        #self.write({'ticket_status_id': 4})

    @api.multi
    def deleted_ticket(self):     
        _logger.info("call to deleted")
        #self.write({'ticket_status_id':7})

#        task = self.task_id
#        task.sudo().write({'stage_id': 8})
        
#        self.send_notification_mail(
#            template_xml_id='email_template_ticket_new',
#            object_class='crm.helpdesk',
#            object_id=self.id,
#            expande={'after_body': 'task annullato'}
#            )
            
    @api.multi
    def refuse_ticket(self):
        _logger.info("call to refused")
        #self.write({'ticket_status_id':7})
        
#        task = self.task_id
#        task.sudo().write({'stage_id': 8})
        
#        self.send_notification_mail(
#            template_xml_id='email_template_ticket_new',
#            object_class='crm.helpdesk',
#            object_id=self.id,
#            expande={'after_body': 'stima rifiutata'}
#            )

