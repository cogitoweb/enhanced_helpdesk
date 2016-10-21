import logging

logger = logging.getLogger('upgrade')

def migrate(cr, version):
    if not version:
        return
    
    logger.info("Updating crm_helpdesk ticket_status_id")
    
    if(version == '8.0.0.1'):
        cr.execute("select max(id) from helpdesk_ticket_status where status_code = 'new'")
        r = cr.fetchone()
        if(r[0] != '1'):
            cr.execute("""delete from helpdesk_ticket_status where id = """ + str(r[0]))

        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = (select id from helpdesk_ticket_status where status_code = 'new') WHERE state = 'draft' """)
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = (select id from helpdesk_ticket_status where status_code = 'app') WHERE state = 'pending' """)
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = (select id from helpdesk_ticket_status where status_code = 'wrk') WHERE state = 'open' """)
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = (select id from helpdesk_ticket_status where status_code = 'ok') WHERE state = 'done' """)
        cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = (select id from helpdesk_ticket_status where status_code = 'xx') WHERE state = 'cancel' """)
    


        
