from odoo import api, fields, models, _


class TerminateContractWizard(models.TransientModel):
    _name = 'terminate.contract.wizard'
    _description = 'Terminate Contract Wizard'

    contract_id = fields.Many2one('contract.details')
    contract_start_date = fields.Date(string="Contract Start Date", compute='_compute_contract_start_date')
    end_date = fields.Date(string="Contract End Date", default=fields.Date.today())
    credit_note_value = fields.Float(string="Contract Credit Note Value",
                                     compute='_compute_calculated_credit_note_value')
    penalty_days = fields.Integer(string="Penalty Days")
    additional_maintenance_value = fields.Float(string="Additional Maintenance Value")

    @api.depends('contract_id')
    def _compute_contract_start_date(self):
        for wizard in self:
            wizard.contract_start_date = wizard.contract_id.from_date

    @api.depends('contract_start_date', 'end_date', 'penalty_days', 'additional_maintenance_value')
    def _compute_calculated_credit_note_value(self):
        for wizard in self:
            contract = wizard.contract_id
            value_per_day = contract.deposite / 365  # Use total_value here
            contract_value_days = (wizard.contract_start_date - wizard.end_date).days
            contract_value_days += wizard.penalty_days
            credit_note_value = contract_value_days * value_per_day
            credit_note_value += wizard.additional_maintenance_value
            wizard.credit_note_value = credit_note_value

    def terminate_contract(self):
        for wizard in self:
            contract = wizard.contract_id

            journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
            line_vals = {
                'name': 'Credit Note for Terminated Contract',
                'quantity': 1,
                'price_unit': wizard.credit_note_value,
            }
            move_vals = {
                # 'date': self.from_date,
                'ref': 'Credit Note for Terminated Contract',
                'move_type': 'out_invoice',
                'journal_id': journal_id.id,
                'contract_id': contract.id,
                'currency_id': journal_id.currency_id.id or self.env.company.currency_id.id,
                'partner_id': contract.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, line_vals)]
            }
            self.env['account.move'].create(move_vals)

            if contract.property_id:
                contract.unit_id.write({'state': 'rent'})

            # Update history records
            history_ids = self.env['renter.history'].search([('contract_id', '=', contract.id)], limit=1)
            history_ids.state = 'cancel'
            history_ids.is_invoice = True

            # Cleanup history logs
            log = self.env['renter.history'].search([('contract_id', '=', contract.id), ('state', '=', 'cancel')])
            log.unlink()

            contract.write({
                'state': 'terminated',
                # 'end_date': wizard.end_date,
            })
            return {'type': 'ir.actions.act_window_close'}
