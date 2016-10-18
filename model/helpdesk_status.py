from openerp import models, fields, api, SUPERUSER_ID
from openerp.tools.translate import _

class HelpdeskStatus(models.Model):
	"""docstring for HelpdeskStatus"""
	_name = 'helpdesk.ticket.status'
	_rec_name = 'status_name' # Used to map id, value


	status_name = fields.Char('Nome Stato', required=True, translate=True)
	status_code = fields.Char('Codice Stato', required=True, translate=True)
	status_description =  fields.Text('Descrizione', translate=True)
	status_deadline = fields.Char('Durata' , translate=True, help="Deadline in Minutes")
	status_order = fields.Integer('Ordinamento')


	
