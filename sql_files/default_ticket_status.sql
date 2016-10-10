INSERT INTO  helpdesk_ticket_status(id,status_name)
VALUES ('1',  'Nuovo')
ON CONFLICT (id) DO NOTHING;
INSERT INTO  helpdesk_ticket_status(id,status_name)
VALUES ('2', 'Presa in carico')
ON CONFLICT (di) DO NOTHING;
INSERT INTO  helpdesk_ticket_status(id,status_name)
VALUES ('3', 'in approvazione')
ON CONFLICT (id) DO NOTHING;
INSERT INTO  helpdesk_ticket_status(id,status_name) 
VALUES ('4', 'In lavorazione')
ON CONFLICT (id) DO NOTHING;
INSERT INTO  helpdesk_ticket_status(id,status_name)
VALUES ('5', 'Consegna')
ON CONFLICT (id) DO NOTHING;
INSERT INTO  helpdesk_ticket_status(id,status_name)
VALUES ('6', 'Completato')
ON CONFLICT (id) DO NOTHING;
INSERT INTO  helpdesk_ticket_status(id,status_name) 
VALUES ('7', 'Anullato')
ON CONFLICT (id) DO NOTHING;  