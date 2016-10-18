def migrate(cr, version):
    if not version:
        return

    
#    cr.execute("""INSERT INTO  helpdesk_ticket_status(id,status_name) VALUES ('1', 'Nuovo')  """)
#    cr.execute("""INSERT INTO  helpdesk_ticket_status(id,status_name) VALUES ('2', 'Presa in carico') """)           
#    cr.execute("""INSERT INTO  helpdesk_ticket_status(id,status_name) VALUES ('3', 'in approvazione') """)     
#    cr.execute("""INSERT INTO  helpdesk_ticket_status(id,status_name) VALUES ('4', 'In lavorazione')  """) 
#    cr.execute("""INSERT INTO  helpdesk_ticket_status(id,status_name) VALUES ('5', 'Consegna')  """)   
#    cr.execute("""INSERT INTO  helpdesk_ticket_status(id,status_name) VALUES ('6', 'Completato')   """)  
#    cr.execute("""INSERT INTO  helpdesk_ticket_status(id,status_name) VALUES ('7', 'Anullato')  """)           

    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 1 WHERE state = 'draft' """)
    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 3 WHERE state = 'pending' """)
    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 4 WHERE state = 'open' """)
    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 6 WHERE state = 'done' """)
    cr.execute(""" UPDATE crm_helpdesk SET ticket_status_id = 7 WHERE state = 'cancel' """)


        
