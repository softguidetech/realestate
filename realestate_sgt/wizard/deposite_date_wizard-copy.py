# -*- coding: utf-8 -*-

from odoo import models, fields, api
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
        # Make the Internal Transfer Between PDC account(s) (type: bank) and Bank account (account set on the selected journal)
        # --- Sending Operation ---
        send_vals = {
            'payment_type':'outbound',
            'is_internal_transfer':True,
            'date':self.deposit_date,
            'amount':self.payment_id.amount,
            'ref':self.payment_id.ref
        }

        bank_journal_id = self.bank_journal
        pyment_journal_id = self.payment_id.journal_id


        _logger.warning('nLog: deposit_cheque ==> send_vals {0}'.format(send_vals))
        _logger.warning('nLog: deposit_cheque ==> payment_id.payment_type  {0}'.format(self.payment_id.payment_type))

        if self.payment_id.payment_type == 'inbound':
            send_vals.update({'journal_id': pyment_journal_id.id})
            send_vals.update({'destination_journal_id': bank_journal_id.id})
        elif self.payment_id.payment_type == 'outbound':
            send_vals.update({'journal_id': bank_journal_id.id})
            send_vals.update({'destination_journal_id': pyment_journal_id.id})

        _logger.warning('nLog: deposit_cheque ==> send_vals[after payment_type] {0}'.format(send_vals))


        send_pay_id = self.env['account.payment'].create(send_vals)
        _logger.warning('nLog: deposit_cheque ==> send_pay_id {0}'.format(send_pay_id))
        _logger.warning('nLog: deposit_cheque ==> send_pay_id {0}'.format(send_pay_id.name))
        _logger.warning('nLog: deposit_cheque ==> send_pay_id.journal_id {0}'.format(send_pay_id.journal_id))
        

        send_pay_id.action_post()

        _logger.warning('nLog: deposit_cheque ==> after send_pay_id.action_post {0}'.format(send_pay_id))

        # --- Receiving Operation ---
        receive_vals = {
            'payment_type':'inbound',
            'is_internal_transfer':True,
            'date':send_pay_id.date,
            'journal_id':self.bank_journal.id,
            'amount':send_pay_id.amount,
            'ref':send_pay_id.ref
        }
        _logger.warning('nLog: deposit_cheque ==> receive_vals {0}'.format(receive_vals))




        if self.payment_id.payment_type == 'inbound':
            receive_vals.update({'journal_id':bank_journal_id.id})
            receive_vals.update({'destination_journal_id':pyment_journal_id.id})
        elif self.payment_id.payment_type == 'outbound':
            receive_vals.update({'journal_id': pyment_journal_id.id})
            receive_vals.update({'destination_journal_id':bank_journal_id.id})
        recieve_pay_id = self.env['account.payment'].create(receive_vals)
        recieve_pay_id.action_post()
        self.payment_id.write({
                            'deposit_date': self.deposit_date,
                            'pdc_state':'deposited'})
