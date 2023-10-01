# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    is_property_maintenance = fields.Boolean(string='Property Maintenance')
    is_unit_maintenance = fields.Boolean(string='Unit Maintenance')
    is_floor_maintenance = fields.Boolean(string='Floor Maintenance')
    property_id = fields.Many2one('product.product' , string='Property')
    unit_id = fields.Many2one('property.unit',  string='Unit')
    floor_id = fields.Many2one('property.floor',string='Floor')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    vendor_bill_ids = fields.One2many('account.move', 'repair_cus_order_id', string='Vendor Bills')
    move_count = fields.Integer("Vendor bill", compute='_compute_move_count')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")

    # @api.depends('vendor_bill_ids')
    # def _compute_move_count(self):
    #     for rec in self:
    #         rec.move_count = len(rec.vendor_bill_ids)

    def action_create_move(self):
        return {
            'name': 'Create Vendor Bill',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_in_invoice_bill_tree').id,
            'res_model': 'account.move',
            # 'res_id': contract_id.id,
            'type': 'ir.actions.act_window',
            # 'target': 'new',
            # 'context': {
            #     'default_partner_id': self.partner_id.id,
            #     'default_amount_total': self.amount_total,
            #     'default_currency_id': self.company_id.currency_id.id,
            #     'default_repair_order_id': self.id,
            #     'default_property_id': self.property_id.id,
            #     'default_unit_id': self.unit_id.id,
            #     'default_move_line_ids': [(0, 0, {
            #         'analytic_account_id': self.analytic_account_id.id})],
            # }
        }


class AccountMove(models.Model):
    _inherit = 'account.move'

    repair_cus_order_id = fields.Many2one('repair.order')


