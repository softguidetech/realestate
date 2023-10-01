# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError, RedirectWarning

from datetime import datetime
import logging
_logger = logging.getLogger(__name__)





class deposit_date_wizard(models.TransientModel):
    _name = 'deposit.date.wizard'
    _description  = 'Deposit Cheque'
    
    deposit_date = fields.Date('Deposit Date')
    bank_journal = fields.Many2one('account.journal',string='Journal')
    payment_id = fields.Many2one('account.payment')





    def deposit_cheque(self):

        account_payment_transfer_info = {
            'is_internal_transfer':True,
            'date':self.deposit_date,
            'amount':self.payment_id.amount,
            'ref':self.payment_id.ref
        }

        bank_journal_id = self.bank_journal
        payment_journal_id = self.payment_id.journal_id

        if not (bank_journal_id and payment_journal_id):
            raise ValidationError(_('Bank Journal or Payment Journal is missing'))


        if self.payment_id.payment_type == 'inbound':
            account_payment_transfer_info.update({'payment_type': 'outbound'})
            account_payment_transfer_info.update({'journal_id': payment_journal_id.id})
            account_payment_transfer_info.update({'destination_journal_id': bank_journal_id.id})

        elif self.payment_id.payment_type == 'outbound':
            account_payment_transfer_info.update({'payment_type': 'inbound'})
            account_payment_transfer_info.update({'journal_id': payment_journal_id.id})
            account_payment_transfer_info.update({'destination_journal_id': bank_journal_id.id})       


        account_payment_transfer = self.env['account.payment'].create(account_payment_transfer_info)
        account_payment_transfer.action_post()

        self.payment_id.write({
                            'deposit_date': self.deposit_date,
                            'pdc_state':'deposited'})







        # # Make the Internal Transfer Between PDC account(s) (type: bank) and Bank account (account set on the selected journal)
        # # --- Sending Operation ---
        # send_vals = {
        #     'payment_type':'outbound',
        #     'is_internal_transfer':True,
        #     'date':self.deposit_date,
        #     'amount':self.payment_id.amount,
        #     'ref':self.payment_id.ref
        # }
        # if self.payment_id.payment_type == 'inbound':
        #     send_vals.update({'journal_id':self.payment_id.journal_id.id})
        # elif self.payment_id.payment_type == 'outbound':
        #     send_vals.update({'journal_id':self.bank_journal.id})
        # send_pay_id = self.env['account.payment'].create(send_vals)
        # send_pay_id.action_post()

        # # --- Receiving Operation ---
        # receive_vals = {
        #     'payment_type':'inbound',
        #     'is_internal_transfer':True,
        #     'date':send_pay_id.date,
        #     'journal_id':self.bank_journal.id,
        #     'amount':send_pay_id.amount,
        #     'ref':send_pay_id.ref
        # }
        # if self.payment_id.payment_type == 'inbound':
        #     receive_vals.update({'journal_id':self.bank_journal.id})
        # elif self.payment_id.payment_type == 'outbound':
        #     receive_vals.update({'journal_id': self.payment_id.journal_id.id})
        # recieve_pay_id = self.env['account.payment'].create(receive_vals)
        # recieve_pay_id.action_post()
        # self.payment_id.write({
        #                     'deposit_date': self.deposit_date,
        #                     'pdc_state':'deposited'})
