# -*- coding: utf-8 -*-

from datetime import date, datetime
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo import exceptions
from odoo.exceptions import Warning


class hr_employee(models.Model):
    
    _inherit                        = 'hr.employee'
    
    father_name                     = fields.Char(string=u'Nom du père')
    mother_name                     = fields.Char(string=u'Nom de la mère')
    
    conjoint_s_name                 = fields.Char(string='Nom du conjoint')
    spouse_s_name                   = fields.Char(string='Nom de l\'epoux(se)')
    matricule                       = fields.Char(string='Matricule')
    personal_fixed_phone            = fields.Char(string='Téléphone fixe personnel')
    cnaps_number                    = fields.Char(string='Numéro CNaPS')
    groupe_sanguin                  = fields.Char(string='Groupe sanguin')
    
    psi_category_details = fields.Many2one(related='job_id.psi_category',string='Titre de la Catégorie')
    psi_category = fields.Selection(related='psi_category_details.psi_professional_category')
    
    emergency_contact_id            = fields.Many2one('hr.person.information', string=u'Personne à contacter en cas d\'urgence',
         help='Person to contact in case of emergency')
    
    beneficiary_of_death_benefit_id = fields.Many2one('hr.person.information', string=u'Bénéficiaire d\'indemnité en cas de décès',
         help='Beneficiary of death benefit')
    
    information_about_children_id   = fields.Many2one('hr.person', string=' Informations sur les enfants',help='Information about children')
    
    information_cin_id              = fields.Many2one('hr.information.cin', string='Information sur CIN',help='Information about CIN')

    marital = fields.Selection([
        ('single', u'Célibataire'),
        ('married', u'Marié(e)'),
        ('separated', u'Séparé(e)'),
        ('widower', 'Veuf(ve)'),
        ('divorced', u'Divorcé(e)')
    ], string='Situation de famille', track_visibility='always')
    
    state = fields.Selection([
                              ('open','Open'),
                              ('close','Close')
                              ],track_visibility='always')

    address_home_id = fields.Many2one('res.partner', string='Home Address', track_visibility='always')
    personal_phone = fields.Char(string='Téléphone personnel', track_visibility='always')
    
    sexe = fields.Selection([
        ('masculin', 'Masculin'),
        ('feminin', u'Féminin')
     ], string='Sexe') 

    personal_information        = fields.Boolean(default=False, string="Fiche de renseignements personnels")
    id_photos                   = fields.Boolean(default=False, string=u"Photos d'identité")
    certificate_residence       = fields.Boolean(default=False, string=u"Certificat de résidence")
    marriage_certificate        = fields.Boolean(default=False, string="Acte de mariage ou copie de livret de famille")
    cin                         = fields.Boolean(default=False, string="Copie CIN")
    work_certificate            = fields.Boolean(default=False, string="Copies Certificats de travail")
    qualifications              = fields.Boolean(default=False, string=u"Copies Diplômes ")
    criminal_records            = fields.Boolean(default=False, string="Casier judiciaires")
    card_cnaps                  = fields.Boolean(default=False, string="Copie Carte CNAPS ")
    birth_certificate_children  = fields.Boolean(default=False, string="Acte de naissance des enfants ")
    details_declaration_interet = fields.One2many('hr.declaration.interest', 'employee_id', string=u"Déclaration d\'intérêt", track_visibility="onchange")
    details_cours_ethique       = fields.One2many("hr.cours.ethique", 'employee_id', string=u"Cértificat de cours d\'éthique", track_visibility="onchange")
    #TODO verification certficats
    ethics_course_certificate   = fields.Boolean(default=False, string=u"Certificat du cours d'éthique")
    attachment_number           = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids              = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.employee')], string='Attachments', track_visibility='always')
    
    sanctions_data = fields.One2many('hr.contract.sanction.data', 'employee_id', string='', track_visibility='always')
    psi_bridger_insight = fields.One2many('hr.employee.bridger.insight', 'employee_id',"Bridger insight")
    
    psi_budget_code_distribution = fields.Many2one(related="job_id.psi_budget_code_distribution", store=True)

    psi_contract_type = fields.Selection(related="job_id.psi_contract_type", string="Type de contrat",store=True)
    
    all_files_checked = fields.Boolean(compute='_all_checked_files', string=u"Pièces completes")

    @api.model
    def create(self, vals):
        employee = super(hr_employee, self).create(vals)
        return employee
    
    @api.multi
    def write(self, vals):
        employee = super(hr_employee, self).write(vals)
        return employee
    
    # fonction remove sanction after period MONTHS
    def _remove_sanction_data(self, period): #period en mois
        employee_obj = self.env["hr.employee"]
        employees = employee_obj.search([])
        sanctions_data_obj = self.env["hr.contract.sanction.data"]
        today = datetime.today()
        n = 0
        for employee in employees:
            list_sanction = sanctions_data_obj.search([('employee_id', '=', employee.id)])
            for sanction in list_sanction:
                if sanction.sanction_date != False:
                    s_date = datetime.strptime(sanction.sanction_date,"%Y-%m-%d")
                    if (today.year - s_date.year) * 12 + today.month - s_date.month >= period:
                        sanction.unlink()
  
    @api.one
    @api.constrains('personal_information')   
    def _get_not_checked_files(self):      
        list_not_checked = list()
        for record in self:  
            certificate_ethics = False
            declaration_obj = self.env["hr.declaration.interest"]
            declarations = declaration_obj.search([('employee_id','=',record.id)])
            
            for declaration in declarations:               
                date_str = str(declaration.year)
                if date_str:
                    if date_str == str(datetime.now().year):
                        certificate_ethics = True
                        break
                    else:
                        certificate_ethics = False
            dict ={
                       'personal_information'       : record.personal_information,
                       'id_photos'                  : record.id_photos,
                       'certificate_residence'      : record.certificate_residence,
                       'marriage_certificate'       : record.marriage_certificate,
                       'cin'                        : record.cin,
                       'work_certificate'           : record.work_certificate,
                       'qualifications'             : record.qualifications,
                       'criminal_records'           : record.criminal_records,
                       'card_cnaps'                 : record.card_cnaps,
                       'birth_certificate_children' : record.birth_certificate_children,
                       'details_certificate_ethics' : certificate_ethics
                   }
            
            for key, value in dict.items() :
                if value == False:
                    list_not_checked.append(key)      
        return list_not_checked

    @api.multi
    def _get_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'hr.employee'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = dict((res['res_id'], res['res_id_count']) for res in read_group_res)
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)
 
    @api.multi 
    def action_get_attachment_tree_view(self):    
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {'default_res_model': self._name, 'default_res_id': self.ids[0]}
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        action['search_view_id'] = (self.env.ref('hr_contract.ir_attachment_view_search_inherit_hr_employee').id, )
        return action
    
    #(R6.) First Rappel au cours d'éthique  
    def _send_first_email_collaborator(self, automatic=False):
        employees = self.env['hr.employee'].search([])
        print "Verification mail 1 collaborateur"
        for record in employees:
            date_create = record.create_date
            date_create_employee = datetime.strptime(date_create,"%Y-%m-%d %H:%M:%S")
            date_create_employee_time = datetime(
                    year=date_create_employee.year, 
                    month=date_create_employee.month,
                    day=date_create_employee.day,
                )
            date_to_notif = date_create_employee_time - relativedelta(days=0) #15 days
            if date_to_notif.date() == datetime.today().date():
                files_not_checked = record._get_not_checked_files()
                for list_not_check in files_not_checked:
                    if len(list_not_check) > 0:
                        template = self.env.ref('hr_employee_psi.custom_template_rappel_collab_1')
                        self.env['mail.template'].browse(template.id).send_mail(record.id, force_send=True)
        if automatic:
            self._cr.commit()

    #(R8.) Second Rappel au cours d'éthique
    def _send_second_email_collaborator(self, automatic=False):
        employees = self.env['hr.employee'].search([])
        print "Verification mail 2 collaborateur"
        for record in employees:  
            date_create = record.create_date
            date_create_employee = datetime.strptime(date_create,"%Y-%m-%d %H:%M:%S")
            date_create_employee_time = datetime(
                    year=date_create_employee.year, 
                    month=date_create_employee.month,
                    day=date_create_employee.day,
                )
            date_to_notif = date_create_employee_time - relativedelta(weeks=0) #3 weeks
#            print date_to_notif.date() ,' # ', datetime.today().date()
            if date_to_notif.date() == datetime.today().date():
                certificate_ethics = False
                declaration_obj = self.env["hr.declaration.interest"]
                declarations = declaration_obj.search([('employee_id','=',record.id)])
                for declaration in declarations:               
                    date_str = str(declaration.year)
                    if date_str:
                        if date_str == str(datetime.now().year):
                            certificate_ethics = True
                if not certificate_ethics:
                    template = self.env.ref('hr_employee_psi.custom_template_rappel_collab_2')
                    self.env['mail.template'].browse(template.id).send_mail(record.id, force_send=True)
        if automatic:
            self._cr.commit()
    
    # add declaration interest every year
    def _add_declaration_interest(self, automatic=False):
        print "Verification declaration interet/1ans"
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            date_create = employee.create_date
            date_create_employee = datetime.strptime(date_create,"%Y-%m-%d %H:%M:%S")
            date_now = datetime.now().date()  
            one_week_after = date_create_employee.date() + timedelta(days=7)         
            if date_now == date_create_employee.date() or date_now == one_week_after:
                declaration = self.details_declaration_interet
                declaration_interet = declaration.verify_year_declaration()
                if not declaration_interet:
                    print "mail ", date_now.year
                    template = self.env.ref('hr_employee_psi.custom_template_add_declaration_interest')
                    self.env['mail.template'].browse(template.id).send_mail(employee.id, force_send=True)
        if automatic:
            self._cr.commit()
            
    # add certificate etich every 2 year
    def _add_certificate_ethics (self, automatic=False):
        print "Verification certificat cours d'Ã©thique/2ans"
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            date_create = employee.create_date
            date_create_employee = datetime.strptime(date_create,"%Y-%m-%d %H:%M:%S")
            date_now = datetime.now().date()
            one_week_after = date_create_employee.date() + timedelta(days=7) 
            if date_now == date_create_employee.date() or date_now == one_week_after: 
                cours_ethique = self.details_cours_ethique
                ethics = cours_ethique.verify_year_certificate_ethics()
                if not ethics:
                    print 'mail'
                    template = self.env.ref('hr_employee_psi.custom_template_add_certificate_ethics')
                    self.env['mail.template'].browse(template.id).send_mail(employee.id, force_send=True)               
                #test
#                mail_failed_list = self.env['mail.mail'].search([('state', '=', 'exception')])
#                for failed_mail in mail_failed_list:
#                    failed_mail.state = 'outgoing'
        if automatic:
            self._cr.commit()
                
class Person(models.Model):

     _name         = 'hr.person'
     
     name          = fields.Char(string='Nom',required=True)
     date_of_birth = fields.Date(string="Date de naissance",required=True)    
     sex           = fields.Selection([
        ('M', 'Masculin'),
        ('F', u'Féminin')
     ], string='Genre')    

    
class PersonInformation(models.Model):
   
    _inherit      = 'hr.person'
    _name         = 'hr.person.information'
    
    address       = fields.Char(string='Adresse')
    contact       = fields.Integer(string='Contact')
    
    relation      = fields.Selection([
        ('enfant', 'Enfant'),
        ('famille', 'Famille'),
        ('conjoint', 'Conjoint')
    ], string='Relation')
    

class InformationCin(models.Model):
    
    _name               = 'hr.information.cin'
    
    name             = fields.Char(u'Numéro', size=64, required=True)
    date_of_issue       = fields.Date(string=u"Date d’émission")
    place_of_issue      = fields.Char(string=u'Lieu d’émission')
    end_of_validity     = fields.Date(string=u"Fin de validité")
    duplicata           = fields.Boolean(string="Duplicata (O/N)")
    date_of_duplicata   = fields.Date(string="Date de duplicata")
    
class ContractTypeSanction(models.Model):

    _name = 'hr.contract.type.sanction'
    _description = 'Liste des sanctions'

    name = fields.Char(string='Nom de la sanction')
    
class SanctionData(models.Model):

    _name = 'hr.contract.sanction.data'
    _order = 'sanction_date desc'

    name = fields.Char(string='Nom de la sanction')
    sanction_date = fields.Date(string='Date de la sanction')
    
    sanction_type_id = fields.Many2one('hr.contract.type.sanction', string='Sanction')
    
    sanction_objet = fields.Char(string='Objet')
    sanction_commentaire = fields.Text(string='Commentaires')

    employee_id = fields.Many2one('hr.employee')
    
class hr_declaration_interest(models.Model):
    
    _name = "hr.declaration.interest"
    _description = u"Declaration d'intérêt - Cours d'éthique"
    
    name = fields.Char(string=u'Nom', required=True)
    employee_id = fields.Many2one('hr.employee', string=u'Employé', readonly=True)
    date_add = fields.Date(string=u'Date d\'ajout',default=lambda *a: datetime.now())
    year =  fields.Selection([
                              (num, str(num)) for num in range(2010, (datetime.now().year)+1 
                                                             )], string=u'Année', required="True", default=datetime.now().year)
    certificate_ethics_file = fields.Binary(string=u'Cértificat de cours d\'éthique')
    declaration_interet = fields.Binary(string=u'Déclaration d\'intérêt')
    checked_current_year = fields.Boolean(string='Check')
    
    b_edit = fields.Boolean(default=False)

    @api.multi
    def write(self, vals):
        declaration = self.verify_year_declaration()
        if declaration == True:
            #self.b_edit = True
            vals['b_edit'] = True                  
            super(hr_declaration_interest, self).write(vals)
            return True
        else : 
            raise Warning(_(u'Vous avez déjà rempli le formulaire de déclaration cette année'))
            return False
        
    def verify_year_declaration(self):
        res = False
        for record in self:
            declaration_obj = self.env["hr.declaration.interest"]
            declarations = declaration_obj.search([('employee_id','=',record.employee_id.name)]) 
            print declarations
            if len(declarations) == 1:
                res = True
            else:
                for declaration in declarations[:-1]:               
                    date_str = str(declaration.year)
                    if date_str:
                        if str(record.year) == date_str:
                            res = False
                        else: 
                            res = True
        return res

class hr_cours_ethique(models.Model):
    
    _name = "hr.cours.ethique"
    _description = u"Cours d'éthique"
    
    name = fields.Char(string=u'Nom', required=True)
    employee_id = fields.Many2one('hr.employee', string=u'Employé', readonly=True)
    date_add = fields.Date(string=u'Date d\'ajout',default=lambda *a: datetime.now())
    year =  fields.Selection([
                              (num, str(num)) for num in range(2010, (datetime.now().year)+1 
                                                             )], string=u'Année', required="True", default=datetime.now().year)
    certificate_ethics_file = fields.Binary(string=u'Cértificat de cours d\'éthique')
    checked_current_year = fields.Boolean(string='Check')
    
    b_edit = fields.Boolean(default=False)

    @api.multi
    def write(self, vals):
        declaration = self.verify_year_certificate_ethics()
        
    def verify_year_certificate_ethics(self):
        res = False
        for record in self:
            declaration_obj = self.env["hr.declaration.interest"]
            declarations = declaration_obj.search([('employee_id','=',record.employee_id.name)]) 
            print declarations
            if len(declarations) == 1:
                res = True
            else:
                for declaration in declarations[:-1]:               
                    date_str = str(declaration.year)
                    if date_str:
                        if str(record.year) == date_str:
                            res = False
                        else: 
                            res = True
        return res
    
        
class BrigerInsight(models.Model):
    _name = 'hr.employee.bridger.insight'
    
    date = fields.Date(u'Date de vérification')
    result = fields.Selection([
        ('oui', 'OUI'),
        ('non', 'NON')
       ], string=u'Résultat')    
    employee_id = fields.Many2one('hr.employee')
