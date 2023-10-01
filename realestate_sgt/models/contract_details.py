# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class RentContract(models.Model):
    _name = 'contract.contract'
    _description = 'Contract'

    name = fields.Char("Name", required=True)
    contract_type = fields.Selection([('monthly', "Monthly"), ('yearly', "Yearly")], default="monthly")
    month = fields.Integer("#Month", default=1)
    year = fields.Integer('#Year', default=1)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(RentContract, self).create(vals_list)
        if res:
            if res.contract_type == 'monthly':
                if res.month <= 0:
                    raise UserError(_("Please enter valid month in number...!"))
            if res.contract_type == 'yearly':
                if res.month <= 0:
                    raise UserError(_("Please enter valid year in number...!"))
        return res
        # make commit changes 


class ContractDetails(models.Model):
    _name = 'contract.details'
    _description = "Contract Details"

    name = fields.Char()
    contract_id = fields.Many2one('contract.contract', required=True)
    date = fields.Date("Current Date", default=datetime.today().date())
    from_date = fields.Date("Start Date", required=True)
    to_date = fields.Date("Expired Date", required=True)
    property_id = fields.Many2one('product.product', required=True,
                                  domain=[('is_property', '=', True), ('property_book_for', '=', 'rent'),
                                          ('state', '!=', 'reserve')])
    unit_id = fields.Many2one('property.unit', string='Unit')
    partner_id = fields.Many2one('res.partner', string="Property Renter", required=True)
    renewal_date = fields.Date("Renewal Date")
    owner_id = fields.Many2one('res.partner', string="Owner", required=True)
    rent_price = fields.Float(readonly=True)
    deposite = fields.Float("Total Rent", required=False)
    state = fields.Selection([('new', "New"), ('running', "Running"), ('expire', "Expire"), ('cancel', 'Cancelled'),
                              ('terminated', 'Terminated')], default="new")
    contract_month = fields.Integer("Contract Month")
    discount_offer = fields.Float("Discount Offer (%)")
    offer_price = fields.Float("Rent Offer")
    offer_name = fields.Char()
    invoice_count = fields.Integer("Invoice", compute='_compute_invoice_count')
    credit_note_count = fields.Integer("Invoice", compute='_compute_credit_note_count')
    pdc_payment_count = fields.Integer("PDC", compute='_compute_pdc_payment_count')
    payment_ids = fields.Many2many('account.payment', string='Payments')
    payment_count = fields.Integer("Payment Plans", compute='_compute_payment_count')
    depposit_jrnl_count = fields.Integer("Depposit Journal entries", compute='_compute_deposit_journal_entries')
    accured_jrnl_count = fields.Integer("Accured Journal entries", compute='_compute_accured_journal_entries')
    number_of_cheques = fields.Integer(string="Number of Cheque")
    document_ids = fields.Many2many('contract.document', 'contract_document_default_rel', 'contract_id', 'document_id')
    company_id = fields.Many2one('res.company', related='unit_id.company_id')

    def set_state_to_running_expire(self):
        records_to_update_runing = self.search([('from_date', '<=', fields.Date.today()), ('state', '=', 'new')])
        records_to_update_runing.write({'state': 'running'})
        records_to_update_expire = self.search(
            [('to_date', '<=', fields.Date.today()), ('state', 'in', ['new', 'running'])])
        records_to_update_expire.write({'state': 'expire'})
        mistakenly_expired_records = self.search([('to_date', '>', fields.Date.today()), ('state', '=', ['expire'])])
        for rec in mistakenly_expired_records:
            if rec.from_date <= fields.Date.today():
                rec.state = 'running'
            else:
                rec.state = 'new'

    @api.depends('unit_id.deposit')
    def _compute_deposite(self):
        for record in self:
            record.deposite = record.unit_id.deposit

    @api.depends()
    def _compute_invoice_count(self):
        for rec in self:
            invoices = self.env['account.move'].sudo().search(
                [('contract_id', '=', self.id), ('is_deposit', '=', False), ('is_accrued', '=', False),
                 ('is_credit_note', '=', False)])
            rec.invoice_count = len(invoices)

    @api.depends()
    def _compute_credit_note_count(self):
        for rec in self:
            credit_notes = self.env['account.move'].sudo().search(
                [('contract_id', '=', self.id), ('is_credit_note', '!=', False),('move_type', '=', 'out_refund')])
            rec.credit_note_count = len(credit_notes)
    @api.depends()
    def _compute_pdc_payment_count(self):
        for rec in self:
            pdc_payments = self.env['account.payment'].search([('is_pdc_payment', '=',True),('partner_id', '=',rec.partner_id.id)])
            rec.pdc_payment_count = len(pdc_payments)        

    # @api.depends()
    # def _compute_pdc_payment_count(self):
    #     for rec in self:
    #         pdc_payments = self.env['pdc.account.payment'].search([('contract_id', '=', rec.id)])
    #         rec.pdc_payment_count = len(pdc_payments)

    @api.depends()
    def _compute_deposit_journal_entries(self):
        for rec in self:
            depposit_journals = self.env['account.move'].sudo().search(
                [('contract_id', '=', self.id), ('partner_id', '=', self.partner_id.id), ('is_deposit', '=', True)])
            rec.depposit_jrnl_count = len(depposit_journals)

    @api.depends()
    def _compute_accured_journal_entries(self):
        for rec in self:
            accured_journals = self.env['account.move'].sudo().search(
                [('contract_id', '=', self.id), ('partner_id', '=', self.partner_id.id), ('is_accrued', '=', True)])
            rec.accured_jrnl_count = len(accured_journals)

    @api.depends()
    def _compute_payment_count(self):
        for rec in self:
            payment_plan_ids = self.payment_ids
            rec.payment_count = len(payment_plan_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('contract.details') or _('New')
        result = super(ContractDetails, self).create(vals_list)
        return result

    def unlink(self):
        for line in self:
            if line.state != 'new':
                raise UserError(_('You cannot delete property contract (name: %s)') % (line.name,))
        return super(ContractDetails, self).unlink()

    def expired_contract_remainder(self):
        today_date = datetime.today().date()
        expired_contract = self.env['contract.details'].search([('to_date', '<=', today_date)])
        new_contract = self.env['contract.details'].search(
            [('from_date', '<=', today_date), ('to_date', '>', today_date), ('state', '=', 'new')])
        for rec in new_contract:
            rec.write({'state': 'running'})
        for record in expired_contract:
            record.write({'state': 'expire'})
            template_id = self.env.ref('realestate_sgt.rental_contract_template')
            auther = record.owner_id
            template_id.sudo().with_context(auther=auther).send_mail(record.id, force_send=True)
        return True

    def monthly_maintainance_remainder(self):
        today_date = datetime.today().date()
        running_contract = self.search([('state', '=', 'running')])
        for rec in running_contract:
            if rec.property_id.rent_unit == 'monthly':
                from_date = rec.from_date + relativedelta(months=1)
                if from_date == today_date:
                    template_id = self.env.ref('realestate_sgt.monthly_maintainance_template')
                    auther = rec.property_id.salesperson_id
                    template_id.sudo().with_context(auther=auther).send_mail(rec.id, force_send=True)
            if rec.property_id.rent_unit == 'yearly':
                from_date = rec.from_date + relativedelta(years=1)
                if from_date == today_date:
                    template_id = self.env.ref('realestate_sgt.yearly_maintainance_template')
                    auther = rec.property_id.salesperson_id
                    template_id.sudo().with_context(auther=auther).send_mail(rec.id, force_send=True)
        return True

    def create_renew_contract(self):
        view_id = self.env.ref('realestate_sgt.renew_contract_wizard')
        if view_id:
            renew_contract_data = {
                'name': _('Renew Contract Configure'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'renew.contract',
                'view_id': view_id.id,
                'target': 'new',
                'context': {
                    'rent_price': self.rent_price,
                    'contract_id': self.contract_id.id,
                    'renter_id': self.partner_id.id,
                    'owner_id': self.owner_id.id,
                    'property_id': self.property_id.id,
                    'name': self.name,
                    'parent_id': self.id,
                },
            }
        return renew_contract_data

    def cancel_contract(self):
        for record in self:
            # Update states
            record.property_id.state = 'rent'
            record.state = 'cancel'
            #  Cancel related invoices and payment installments
            invoices = self.env['account.move'].search(
                [('unit_id', '=', record.unit_id.id), ('contract_id', '=', record.id)])
            if invoices:
                for invoice in invoices:
                    if invoice.state not in ['draft', 'cancel']:
                        invoice.button_draft()  # Set the invoice to draft state
                        invoice.button_cancel()  # Cancel the invoice
                    # Handle related payment installments (PDCs)
                    for payment in invoice.payment_ids:
                        if payment.state not in ['draft', 'cancel']:
                            payment.button_draft()  # Set the payment installment to draft state
                            payment.button_cancel()  # Cancel the payment installment
            # Release the unit (apartment)
            if record.unit_id:
                record.unit_id.update({'state': 'rent'})
            # Update history records
            history_ids = self.env['renter.history'].search([('contract_id', '=', record.id)], limit=1)
            history_ids.state = 'cancel'
            history_ids.is_invoice = True
            # Cleanup history logs
            log = self.env['renter.history'].search([('contract_id', '=', record.id), ('state', '=', 'cancel')])
            log.unlink()
            # Mark the contract as canceled (logically deleted)
            record.write({'state': 'cancel'})

    def stop_upcoming_payments(self, contract):
        # Find upcoming payments related to the contract
        upcoming_payments = self.env['account.payment'].search([
            ('unit_id', '=', self.unit_id.id), ('contract_id', '=', self.id),
            ('state', 'in', ['draft', 'posted']),
        ])
        # Cancel the upcoming payments
        for payment in upcoming_payments:
            if payment.state == 'posted':
                # If the payment is already posted, reverse the journal entries
                payment.button_draft()  # Set the payment to draft
                payment.action_cancel()  # Cancel the payment
            else:
                # If the payment is in draft state, simply cancel it
                payment.action_cancel()
        return True  # Return a flag indicating success

    def refund_remaining_invoice(self, invoice, refund_description):
        journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        credit_note_line_vals_list = []
        for line in invoice.invoice_line_ids:
            credit_note_line_vals = {
                'name': line.name,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }
            credit_note_line_vals_list.append((0, 0, credit_note_line_vals))
        # Create the credit note
        move_vals = {
            'date': fields.Date.today(),
            'payment_reference': refund_description,
            'move_type': 'out_refund',
            'journal_id': journal_id.id,
            'contract_id': self.id,
            'is_credit_note': True,
            'currency_id': journal_id.currency_id.id or self.env.company.currency_id.id,
            'partner_id': self.partner_id.id,
            'invoice_line_ids': credit_note_line_vals_list,
        }
        cre = self.env['account.move'].create(move_vals)
        return True

    def terminate_contract(self):
        for record in self:
            if record.state == 'terminated':
                raise UserError(_("This contract has already been terminated."))
            record.property_id.state = 'rent'
            # Stop upcoming payment plan
            self.stop_upcoming_payments(record)
            # Find remaining invoices
            remaining_invoices = self.env['account.move'].search([
                ('unit_id', '=', record.unit_id.id), ('contract_id', '=', self.id), ('is_credit_note', '=', False),
                ('state', '=', 'posted'),  # Only consider posted invoices
            ])
            # Refund remaining invoice amounts and create a credit note
            refund_description = _("Refund for terminated contract")
            credit_note = None
            for invoice in remaining_invoices:
                credit_note = self.refund_remaining_invoice(invoice, refund_description)
            # Release the unit (apartment)
            if record.unit_id:
                record.unit_id.write({'state': 'rent'})
            # Update history records
            history_ids = self.env['renter.history'].search([('contract_id', '=', record.id)], limit=1)
            history_ids.state = 'cancel'
            history_ids.is_invoice = True
            # Cleanup history logs
            log = self.env['renter.history'].search([('contract_id', '=', record.id), ('state', '=', 'cancel')])
            log.unlink()
            # Mark the contract as terminated (logically deleted)
            record.write({'state': 'terminated'})

    # def terminate_contract(self):
    # 	for record in self:
    # 		record.property_id.state = 'rent'
    # 		# Stop upcoming payment plan
    # 		self.stop_upcoming_payments(record)
    # 		# Find remaining invoices
    # 		remaining_invoices = self.env['account.move'].search([
    # 			('unit_id', '=', record.unit_id.id),('contract_id', '=', self.id),
    # 			('state', '=', 'posted'),  # Only consider posted invoices
    # 		])
    # 		print(remaining_invoices,"111111111111111111111111111111111111111111111111")
    # 		# Refund remaining invoice amounts
    # 		refund_description = _("Refund for terminated contract")
    # 		for invoice in remaining_invoices:
    # 			self.refund_remaining_invoice(invoice, refund_description)
    # 		# Release the unit (apartment)
    # 		if record.unit_id:
    # 			record.unit_id.write({'state': 'rent'})
    # 		# Update history records
    # 		history_ids = self.env['renter.history'].search([('contract_id', '=', record.id)], limit=1)
    # 		history_ids.state = 'cancel'
    # 		history_ids.is_invoice = True
    # 		# Cleanup history logs
    # 		log = self.env['renter.history'].search([('contract_id', '=', record.id), ('state', '=', 'cancel')])
    # 		log.unlink()
    # 		# Mark the contract as canceled (logically deleted)
    # 		record.write({'state': 'terminated'})

    def action_view_invoice(self):
        invoices = self.env['account.move'].sudo().search(
            [('contract_id', '=', self.id), ('is_deposit', '=', False), ('is_accrued', '=', False),
             ('is_credit_note', '=', False)])
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    def action_view_credit_note(self):
        credit_notes = self.env['account.move'].sudo().search(
            [('contract_id', '=', self.id),('is_credit_note', '!=', False)])
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(credit_notes) > 1:
            action['domain'] = [('id', 'in', credit_notes.ids)]
        elif len(credit_notes) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = credit_notes.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_depposit_journals(self):
        depposit_journals = self.env['account.move'].sudo().search(
            [('contract_id', '=', self.id), ('partner_id', '=', self.partner_id.id), ('is_deposit', '=', True)])
        action = self.env.ref('account.action_move_journal_line').read()[0]
        if len(depposit_journals) > 1:
            action['domain'] = [('id', 'in', depposit_journals.ids)]
        elif len(depposit_journals) == 1:
            action['views'] = [(self.env.ref('realestate_sgt.view_account_move_form_inherit').id, 'form')]
            action['res_id'] = depposit_journals.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_accured_journals(self):
        accured_journals = self.env['account.move'].sudo().search(
            [('contract_id', '=', self.id), ('partner_id', '=', self.partner_id.id), ('is_accrued', '=', True)])
        action = self.env.ref('account.action_move_journal_line').read()[0]
        if len(accured_journals) > 1:
            action['domain'] = [('id', 'in', accured_journals.ids)]
        elif len(accured_journals) == 1:
            action['views'] = [(self.env.ref('realestate_sgt.view_account_move_form_inherit').id, 'form')]
            action['res_id'] = accured_journals.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_pdc_payments(self):
        pdc_payments = self.env['account.payment'].search([('is_pdc_payment', '=', True), ('partner_id', '=', self.partner_id.id)])
        action = self.env.ref('realestate_sgt.account_pdc_payment_payable_menu_action').read()[0]
        # action = self.env.ref('customer_post_dated_cheque_app.action_pdc_payment').read()[0]
        if len(pdc_payments) > 1:
            action['domain'] = [('id', 'in', pdc_payments.ids)]
        elif len(pdc_payments) == 1:
            action['views'] = [
                (self.env.ref('realestate_sgt.account_payment_inherit_pdc_form_view').id, 'form')]
                # (self.env.ref('customer_post_dated_cheque_app.view_pdc_account_payment_invoice_form').id, 'form')]
            action['res_id'] = pdc_payments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_payment_plans(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment plan'),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.mapped('payment_ids').ids)],
        }

    def get_contract_details_report(self):
        payment_ids = self.mapped('payment_ids')
        # pdc_payment_ids = self.env['pdc.account.payment'].search([('contract_id', '=', self.id)])
        payment_list = []
        for payment in payment_ids:
            payment_data = {
                'id': payment.id,
                'name': payment.name,
                'date': payment.date,
                'payment_method_line_id': payment.payment_method_line_id.name,
                'partner_id': payment.partner_id.name,
                'amount_company_currency_signed': payment.amount_company_currency_signed,
                'journal': payment.journal_id.name,
                'state': payment.state,
            }
            payment_list.append(payment_data)

        data = {
            'ids': self.ids,
            'model': self._name,
            'payment_list': payment_list or '',
            'form': {
                'name': self.name,
                'contract_name': self.contract_id.name,
                'unit_name': self.unit_id.name,
                'property_name': self.property_id.name,
                'partner_name': self.partner_id.name,
                'owner_name': self.owner_id.name,
                # 'rent_price': self.rent_price,
                'deposit': self.deposite,
                'from_date': self.from_date,
                'to_date': self.to_date,
                'state': self.state,
                'date': self.date,
                'renewal_date': self.renewal_date,
            }
        }
        return self.env.ref('realestate_sgt.report_contract_details').report_action(self, data=data)


class ContractDocument(models.Model):
    _name = 'contract.document'
    _description = "Contract Document"

    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    file = fields.Binary(required=True)
    contract_id = fields.Many2one('contract.details', "Source Document")
