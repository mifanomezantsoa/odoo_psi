# -*- coding: utf-8 -*-

from odoo import models,fields, api
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _

HOURS_PER_DAY = 8

class hr_holidays_psi(models.Model):
    _inherit = "hr.holidays"
    
    psi_category_id = fields.Many2one('hr.psi.category.details','Catégorie professionnelle')
    
    @api.constrains('date_from')
    def _check_date_from(self):
       print "_check_date_from"
       for record in self :
           if record.date_from != False :
               date_from_time = datetime.strptime(record.date_from,"%Y-%m-%d %H:%M:%S")
               date_from = date_from_time.date()
               date_now = datetime.strptime(fields.Date().today(),"%Y-%m-%d")
               between = date_from.day - date_now.day
               if between < 3 :
                  raise ValidationError(u"Vous devez faire le demande de congeés avant 3jours de depart")
     
    @api.multi
    def action_validate(self):
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate1']:
                raise UserError(_('Leave request must be confirmed in order to approve it.'))
            if holiday.state == 'validate1' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

            holiday.write({'state': 'validate'})
            if holiday.double_validation:
                holiday.write({'manager_id2': manager.id})
            else:
                holiday.write({'manager_id': manager.id})
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                meeting_values = {
                    'name': holiday.display_name,
                    'categ_ids': [(6, 0, [holiday.holiday_status_id.categ_id.id])] if holiday.holiday_status_id.categ_id else [],
                    'duration': holiday.number_of_days_temp * HOURS_PER_DAY,
                    'description': holiday.notes,
                    'user_id': holiday.user_id.id,
                    'start': holiday.date_from,
                    'stop': holiday.date_to,
                    'allday': False,
                    'state': 'open',            # to block that meeting date in the calendar
                    'privacy': 'confidential'
                }
                #Add the partner_id (if exist) as an attendee
                if holiday.user_id and holiday.user_id.partner_id:
                    meeting_values['partner_ids'] = [(4, holiday.user_id.partner_id.id)]

                meeting = self.env['calendar.event'].with_context(no_mail_to_attendees=True).create(meeting_values)
                holiday._create_resource_leave()
                holiday.write({'meeting_id': meeting.id})
            elif holiday.holiday_type == 'category':
                leaves = self.env['hr.holidays']
                employees = self.env['hr.employee'].search([])
                for employee in employees: 
                    if employee.psi_category == holiday.psi_category_id.psi_professional_category :
                        values = {
                            'name': holiday.name,
                            'type': holiday.type,
                            'holiday_type': 'employee',
                            'holiday_status_id': holiday.holiday_status_id.id,
                            'date_from': holiday.date_from,
                            'date_to': holiday.date_to,
                            'notes': holiday.notes,
                            'number_of_days_temp': holiday.number_of_days_temp,
                            'parent_id': holiday.id,
                            'employee_id': employee.id
                        }
                        leaves += self.with_context(mail_notify_force_send=False).create(values)
                # TODO is it necessary to interleave the calls?
                leaves.action_approve()
                if leaves and leaves[0].double_validation:
                    leaves.action_validate()
        return True
    
    _sql_constraints = [
        ('type_value', "CHECK( (holiday_type='employee' AND employee_id IS NOT NULL) or (holiday_type='category' AND psi_category_id IS NOT NULL))",
         "The employee or employee category of this request is missing. Please make sure that your user login is linked to an employee."),
        ('date_check2', "CHECK ( (type='add') OR (date_from <= date_to))", "The start date must be anterior to the end date."),
        ('date_check', "CHECK ( number_of_days_temp >= 0 )", "The number of days must be greater than 0."),
    ]
    
    @api.multi
    def name_get(self):
        res = []
        for leave in self:
            res.append((leave.id, _("%s on %s : %.2f day(s)") % (leave.employee_id.name or leave.psi_category_id.psi_professional_category, leave.holiday_status_id.name, leave.number_of_days_temp)))
        return res