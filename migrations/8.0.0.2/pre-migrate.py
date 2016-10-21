import logging

logger = logging.getLogger('upgrade')

def migrate(cr, version):
    if not version:
        return
    
    if(version == '8.0.0.1'):
        cr.execute("""CREATE TABLE helpdesk_ticket_status
            (
              id serial NOT NULL,
              create_uid integer, -- Created by
              create_date timestamp without time zone, -- Created on
              status_deadline character varying, -- Durata
              status_name character varying NOT NULL, -- Nome Stato
              status_code character varying NOT NULL, -- Codice Stato
              write_uid integer, -- Last Updated by
              write_date timestamp without time zone, -- Last Updated on
              status_description text, -- Descrizione
              status_order integer, -- Ordinamento
              CONSTRAINT helpdesk_ticket_status_pkey PRIMARY KEY (id)
            )
            WITH (
              OIDS=FALSE
            )""")
    
        cr.execute("select id from helpdesk_ticket_status where id = 1")
        r = cr.fetchone()
        if not r:
            cr.execute("""INSERT INTO helpdesk_ticket_status(
                    id, create_uid, create_date, status_deadline, status_name, status_code, 
                    write_uid, write_date, status_description, status_order)
                    VALUES (1, 1, now(), null, 'New', 'new', 
                            1, now(), 'New', 1)""")

            cr.execute("SELECT setval('helpdesk_ticket_status_id_seq', (SELECT MAX(id) FROM helpdesk_ticket_status))")



        
