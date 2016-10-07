from openerp.osv import osv
class crm_ticket_status(osv.osv):

    _name = "crm_helpdesk_migrate"
    def _migrate_from_old_satus_to_new(self, cr, uid, ids=None, context=None):
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 1 WHERE state = 'draft' """)
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 3 WHERE state = 'pending' """)
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 4 WHERE state = 'open' """)
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 6 WHERE state = 'done' """)
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 7 WHERE state = 'cancel' """)


        
