import logging

logger = logging.getLogger('upgrade')

def migrate(cr, version):
    if not version:
        return
    
    cr.execute("select id from helpdesk_ticket_status where id = 1")
    r = cr.fetchone()
    if not r:
        cr.execute("""INSERT INTO helpdesk_ticket_status(
                id, create_uid, create_date, status_deadline, status_name, status_code, 
                write_uid, write_date, status_description, status_order)
                VALUES (1, 1, now(), null, 'New', 'new', 
                        1, now(), 'New', 1);""")

        cr.execute("SELECT setval('helpdesk_ticket_status_id_seq', (SELECT MAX(id) FROM helpdesk_ticket_status))")



        
