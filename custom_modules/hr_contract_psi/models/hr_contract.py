# -*- coding: utf-8 -*-

from datetime import timedelta
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

class hr_contract(models.Model):
    _inherit = 'hr.contract'
    
    place_of_work   = fields.Char(string='Lieu d\'affectaction') #lieu d'affectation

    psi_contract_type = fields.Selection([
        ('cdd', 'CDD'),
        ('cdi', 'CDI')
        ('cdi', 'CDI'),
        ('convention_stage','Convention de stage')
    ], string='Type de contrat', help="Type de contrat", track_visibility='onchange')
   
    end_deadline_without_renewal= fields.Boolean(default=False, string="Arrivée de l'échéance sans reconduction")
    conventional_break          = fields.Boolean(default=False, string="Rupture conventionnelle")
    resignation                 = fields.Boolean(default=False, string="Lettre de démission")
    dismissal                   = fields.Boolean(default=False, string="Licenciement")
    death                       = fields.Boolean(default=False, string="Décès")
    retreat                     = fields.Boolean(default=False, string="Retraite")
    
    @api.model
    def create(self, vals):  
        contract = super(hr_contract, self).create(vals)
        self._update_cron_rh_1()
        return contract
    
    @api.multi
    def write(self, vals):
        contract = super(hr_contract, self).write(vals)
        self._update_cron_rh_1()  
        return contract
        
    @api.one
    @api.constrains('name')
    def set_employee_inactif(self):
        """ Set employee inactif
        """
        for record in self:
            contract_obj = self.env['hr.contract']
            employee = record.employee_id
            #employee readonly
            contract = contract_obj.browse([record.id])
        
        return {'type': 'ir.actions.act_window_close'}

    def _update_cron_rh_1(self):
        """ Activate the cron First Email RH + Employee.
        """
        employee = self.employee_id
        cron = self.env.ref('hr_contract_psi.ir_cron_send_email_rh_1', raise_if_not_found=False)
        return cron and cron.toggle(model=self._name, domain=[('name', '!=', '')])
    
    #(R7.) Rappel - enregistrement du profil du collaborateur / complétude
    @api.one
    @api.constrains('name')
    def _send_first_email_rh(self, automatic=False):
        if len(self.employee_id._get_not_checked_files()) > 0:
            template0 = self.env.ref('hr_contract_psi.custom_template_rappel_hr_missing_pieces')
            self.env['mail.template'].browse(template0.id).send_mail(self.id)
            template1 = self.env.ref('hr_contract_psi.custom_template_rappel_collab_missing_pieces')
            self.env['mail.template'].browse(template1.id).send_mail(self.id)
        if automatic:
            self._cr.commit()

    @api.one
    @api.constrains('name')
    def _send_email_trial_date_end(self, automatic=False):
        for record in self:
            if record.trial_date_start:
                date_start = record.trial_date_start
                date_start_trial = datetime.strptime(date_start,"%Y-%m-%d")
                date_start_trial_time = datetime(
                    year=date_start_trial.year, 
                    month=date_start_trial.month,
                    day=date_start_trial.day,
                )
                # Verification selection
                if record.job_id.name == 'Chief Executive Officer':
                    month_to_notif = date_start_trial_time + relativedelta(months=5)  
                    if month_to_notif.date() == datetime.today().date():
                         template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                         self.env['mail.template'].browse(template.id).send_mail(self.id)
                elif record.job_id.name == 'Consultant':
                    month_to_notif = date_start_trial_time + relativedelta(months=3)  
                    if month_to_notif.date() == datetime.today().date():
                         template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                         self.env['mail.template'].browse(template.id).send_mail(self.id)
                elif record.job_id.name == 'Human Resources Manager':
                    month_to_notif = date_start_trial_time + relativedelta(months=2)  
                    if month_to_notif.date() == datetime.today().date():
                         template = self.env.ref('hr_contract_psi.custom_template_trial_date_end')
                         self.env['mail.template'].browse(template.id).send_mail(self.id)
        if automatic:
            self._cr.commit()

    @api.one
    @api.constrains('name')
    def _send_email_end_contract(self, automatic=False):
        print "Send email to mentor - fin contrat"
        for record in self:
            if record.date_end:
                date_end = record.date_end
                date_end_contract = datetime.strptime(date_end,"%Y-%m-%d")
                date_end_contract_time = datetime(
                    year=date_end_contract.year, 
                    month=date_end_contract.month,
                    day=date_end_contract.day,
                )
                month_to_notif = date_end_contract_time - relativedelta(months=1)  
                if month_to_notif.date() == datetime.today().date():
                    template = self.env.ref('hr_contract_psi.custom_template_end_contract')
                    self.env['mail.template'].browse(template.id).send_mail(self.id)
        if automatic:
            self._cr.commit()
            
    def send_email_collaborator(self):
        print "The id contract is : ",self.contract_id
        template = self.env.ref('hr_contract_psi.custom_template_id')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
