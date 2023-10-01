import base64
from datetime import date
from io import BytesIO
from odoo import fields, models
from odoo.tools.misc import xlwt
from xlwt import easyxf
from datetime import datetime


class PdcReport(models.TransientModel):
    _name = 'pdc.report'
    _description = "Post Dated Cheques (PDC) Report"


    def export_pdc_report(self):
        filename = 'PDC Report.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Post Dated Cheques (PDC) Report')
        worksheet.show_grid = False

        # defining various font styles
        header_style = easyxf('font:height 240; align: horiz center;align: vert center;font:bold True;''borders: top thin,bottom thin,right thin;')
        content = easyxf('font:height 200;''borders: top thin,bottom thin,right thin')
        content_right = easyxf('font:height 200;align: horiz right;''borders: top thin,bottom thin,right thin')
        sub_header = easyxf('font:height 210;align: horiz center;pattern: pattern solid, fore_color pale_blue;font:bold True;''borders: top thin,bottom thin,right thin')
        sub_header2 = easyxf('font:height 210;align: horiz left;pattern: pattern solid, fore_color pale_blue;font:bold True;''borders: top thin,bottom thin,right thin,left thin')

        # setting with of the column
        worksheet.col(0).width = 7000
        worksheet.col(1).width = 8000
        worksheet.col(2).width = 5000
        worksheet.col(3).width = 5000
        worksheet.col(4).width = 5000
        worksheet.col(5).width = 5000
        worksheet.col(6).width = 5500
        worksheet.col(7).width = 4000
        worksheet.col(8).width = 2500
        worksheet.col(9).width = 2500
        worksheet.col(10).width = 2500

        worksheet.write_merge(2, 3, 0, 10, 'Post Dated Cheques (PDC) Report', header_style)

        start = datetime.strptime(str(self.start_date), "%Y-%m-%d").strftime('%d-%m-%Y')
        end = datetime.strptime(str(self.end_date), "%Y-%m-%d").strftime('%d-%m-%Y')
        date_data = 'Start Date : ' + str(start) + '\n'
        date_data += 'End Date : ' + str(end)
        worksheet.write_merge(5, 6, 0, 0, date_data, sub_header2)

        counter = 8

        # writing (Labels)
        worksheet.write(counter, 0, '#', sub_header)
        worksheet.write(counter, 1, 'Partner', sub_header)
        worksheet.write(counter, 2, 'Partner Bank', sub_header)
        worksheet.write(counter, 3, 'Cheque Date', sub_header)
        worksheet.write(counter, 4, 'Payment Date', sub_header)
        worksheet.write(counter, 5, 'Due Date', sub_header)
        worksheet.write(counter, 6, 'Cheque Reference', sub_header)
        worksheet.write(counter, 7, 'Journal', sub_header)
        worksheet.write(counter, 8, 'Debit ', sub_header)
        worksheet.write(counter, 9, 'Credit', sub_header)
        worksheet.write(counter, 10, 'Balance', sub_header)

        counter += 1
        search_domain = [('date', '>=', self.start_date),('date', '<=', self.end_date), ('journal_id', 'in', self.journal_ids.ids),('is_pdc_payment','=',True)]
        if len(self.partner_ids) > 0:
            search_domain = search_domain + [('partner_id','in',self.partner_ids.ids)]
        pdc_ids = self.env['account.payment'].search(search_domain)
        
        if pdc_ids:
            balance = self.opening_balance
            worksheet.write_merge(counter, counter, 0, 9, 'Opening Balance', sub_header)
            worksheet.write(counter, 10, ("%.2f" % balance), content_right)
            counter += 1
            for pdc_id in pdc_ids:
                worksheet.write(counter, 0, pdc_id and pdc_id.name or '', content)
                worksheet.write(counter, 1, pdc_id and pdc_id.partner_id and pdc_id.partner_id.name or '', content)
                worksheet.write(counter, 2, pdc_id.partner_bank_id and pdc_id.partner_bank_id.bank_id.name or '', content)
                if pdc_id.cheque_date:
                    cheque_date = datetime.strptime(str(pdc_id.cheque_date), "%Y-%m-%d").strftime('%d-%m-%Y')
                worksheet.write(counter, 3, cheque_date, content)
                if pdc_id.date:
                    payment_date = datetime.strptime(str(pdc_id.date), "%Y-%m-%d").strftime('%d-%m-%Y')
                worksheet.write(counter, 4, payment_date, content)
                if pdc_id.due_date:
                    due_date = datetime.strptime(str(pdc_id.due_date), "%Y-%m-%d").strftime('%d-%m-%Y')
                worksheet.write(counter, 5, payment_date, content)
                worksheet.write(counter, 6, pdc_id.reference or '', content)
                worksheet.write(counter, 7, pdc_id.journal_id.name or '', content)               
                if pdc_id.payment_type == 'outbound':
                    worksheet.write(counter, 8, ("%.2f" % 0), content_right)
                    worksheet.write(counter, 9, ("%.2f" % pdc_id.amount) or '', content_right)
                    balance -= pdc_id.amount
                if pdc_id.payment_type == 'inbound':
                    worksheet.write(counter, 8, ("%.2f" % pdc_id.amount) or '', content_right)
                    worksheet.write(counter, 9, ("%.2f" % 0), content_right)
                    balance += pdc_id.amount
                worksheet.write(counter, 10, ("%.2f" % balance), content_right)
                counter += 1

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        excel_file = base64.encodebytes(fp.read())
        fp.close()
        self.write({'excel_file': excel_file})
        active_id = self.ids[0]
        url = ('web/content/?model=pdc.report&download=true&field=excel_file&id=%s&filename=%s' % (active_id, filename))
        if self.excel_file:
            return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}

    start_date = fields.Date(string="Payment date from", default=date.today(), required=True)
    end_date = fields.Date(string="Payment date to", default=date.today(), required=True)
    excel_file = fields.Binary(string='Excel File')
    journal_ids = fields.Many2many('account.journal', string='Journal(s)', required=True)
    partner_ids = fields.Many2many('res.partner', string='Partner(s)')
    opening_balance = fields.Float('Opening Balance', required=True)
