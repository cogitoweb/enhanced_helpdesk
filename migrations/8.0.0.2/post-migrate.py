import logging

logger = logging.getLogger('upgrade')

def migrate(cr, version):
    if not version:
        return
    
    logger.info("Updating crm_helpdesk ticket_status_id")

    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 1 WHERE state = 'draft' """)
    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 3 WHERE state = 'pending' """)
    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 4 WHERE state = 'open' """)
    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 6 WHERE state = 'done' """)
    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 7 WHERE state = 'cancel' """)


        
