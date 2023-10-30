# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_real_estate_company = fields.Boolean(related='company_id.is_real_estate_company', readonly=False)
    reminder_on_due_date = fields.Boolean(string="Send Mail on Invoice Due Date")
    reminder_after_due_date = fields.Boolean(string="Send Mail After Exceding Invoice Due Date")
    reminder_before_due_date = fields.Boolean(string="Send Mail Before Invoice Due Date")
    reminder_till_come_due_date = fields.Boolean(string="Send Mail Till Not Come Due Date")
    reminder_before_days = fields.Integer(string="Before Days")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        is_real_estate_company = config_parameter.get_param('realestate_sgt.is_real_estate_company')
        reminder_on_due_date = config_parameter.get_param('realestate_sgt.reminder_on_due_date')
        reminder_after_due_date = config_parameter.get_param('realestate_sgt.reminder_after_due_date')
        reminder_before_due_date = config_parameter.get_param('realestate_sgt.reminder_before_due_date')
        reminder_till_come_due_date = config_parameter.get_param('realestate_sgt.reminder_till_come_due_date')
        reminder_before_days = config_parameter.get_param('realestate_sgt.reminder_before_days')
        res.update(is_real_estate_company=is_real_estate_company, reminder_on_due_date=reminder_on_due_date,reminder_before_days=int(reminder_before_days), reminder_before_due_date=reminder_before_due_date,reminder_after_due_date=reminder_after_due_date,reminder_till_come_due_date=reminder_till_come_due_date)
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('realestate_sgt.is_real_estate_company',self.is_real_estate_company)
        self.env['ir.config_parameter'].sudo().set_param('realestate_sgt.reminder_on_due_date', self.reminder_on_due_date)
        self.env['ir.config_parameter'].sudo().set_param('realestate_sgt.reminder_after_due_date', self.reminder_after_due_date)
        self.env['ir.config_parameter'].sudo().set_param('realestate_sgt.reminder_before_due_date', self.reminder_before_due_date)
        self.env['ir.config_parameter'].sudo().set_param('realestate_sgt.reminder_till_come_due_date', self.reminder_till_come_due_date)
        self.env['ir.config_parameter'].sudo().set_param('realestate_sgt.reminder_before_days', self.reminder_before_days)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
