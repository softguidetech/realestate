# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    reminder_on_due_date = fields.Boolean(string="Send Mail on Invoice Due Date")
    reminder_after_due_date = fields.Boolean(string="Send Mail After Exceding Invoice Due Date")
    reminder_before_due_date = fields.Boolean(string="Send Mail Before Invoice Due Date")
    reminder_till_come_due_date = fields.Boolean(string="Send Mail Till Not Come Due Date")
    reminder_before_days = fields.Integer(string="Before Days")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config_parameter = self.env['ir.config_parameter'].sudo()
        reminder_on_due_date = config_parameter.get_param('property_rental_mgt_app.reminder_on_due_date')
        reminder_after_due_date = config_parameter.get_param('property_rental_mgt_app.reminder_after_due_date')
        reminder_before_due_date = config_parameter.get_param('property_rental_mgt_app.reminder_before_due_date')
        reminder_till_come_due_date = config_parameter.get_param('property_rental_mgt_app.reminder_till_come_due_date')
        reminder_before_days = config_parameter.get_param('property_rental_mgt_app.reminder_before_days')
        res.update(reminder_on_due_date=reminder_on_due_date,reminder_before_days=int(reminder_before_days), reminder_before_due_date=reminder_before_due_date,reminder_after_due_date=reminder_after_due_date,reminder_till_come_due_date=reminder_till_come_due_date)
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('property_rental_mgt_app.reminder_on_due_date', self.reminder_on_due_date)
        self.env['ir.config_parameter'].sudo().set_param('property_rental_mgt_app.reminder_after_due_date', self.reminder_after_due_date)
        self.env['ir.config_parameter'].sudo().set_param('property_rental_mgt_app.reminder_before_due_date', self.reminder_before_due_date)
        self.env['ir.config_parameter'].sudo().set_param('property_rental_mgt_app.reminder_till_come_due_date', self.reminder_till_come_due_date)
        self.env['ir.config_parameter'].sudo().set_param('property_rental_mgt_app.reminder_before_days', self.reminder_before_days)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
