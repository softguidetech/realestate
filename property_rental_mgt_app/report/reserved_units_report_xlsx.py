from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo import exceptions
import pytz

class His_Admission_Report_xlsx(models.AbstractModel):
    _name = 'report.property_rental_mgt_app.units_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        unit_ids = data['form']['unit_ids']
        property_id = data['form']['property_id']
        format1_bold = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format1_normal = workbook.add_format({'font_size': 10, 'align': 'left'})
        format2 = workbook.add_format({'font_size': 10, 'align': 'left', })
        merge_format = workbook.add_format(
            {'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'fg_color': 'yellow'})

        sheet = workbook.add_worksheet('Reserved Units Excel Report')
        sheet.merge_range('A1:I3', 'Reserved Units Report', merge_format)

        sheet.write(5, 0, 'SL.NO', format1_bold)
        sheet.write(5, 1, 'Unit', format1_bold)
        sheet.write(5, 2, 'Property', format1_bold)
        sheet.write(5, 3, 'Property Type', format1_bold)
        # Add headings for payment columns
        sheet.write(5, 4, 'Payment Name', format1_bold)
        sheet.write(5, 5, 'Journal', format1_bold)
        sheet.write(5, 6, 'Amount', format1_bold)
        sheet.write(5, 7, 'Payment Date', format1_bold)
        sheet.write(5, 8, 'Payment State', format1_bold)

        sheet.set_row(0, 20)
        sheet.set_row(1, 30)
        sheet.set_column(1, 0, 5)
        sheet.set_column(1, 1, 13)
        sheet.set_column(1, 2, 13)
        sheet.set_column(1, 3, 13)
        sheet.set_column(1, 4, 13)
        sheet.set_column(1, 5, 13)
        sheet.set_column(1, 6, 13)
        sheet.set_column(1, 7, 13)
        sheet.set_column(1, 8, 13)

        unit_domain = []
        unit_domain.append(('state', '=', 'reserve'))
        if property_id:
            unit_domain.append(('property_id', '=', property_id))
        if unit_ids:
            unit_domain.append(('id', 'in', unit_ids))
        if unit_domain:
            reserved_units = self.env['property.unit'].search(unit_domain)

        if reserved_units:

            sl_number = 1
            count = 6
            for r_unit in reserved_units:
                sheet.write(count, 0, sl_number, format1_normal)
                sheet.write(count, 1, r_unit.name or " ", format1_normal)
                sheet.write(count, 2, r_unit.property_id.name or " ", format1_normal)
                sheet.write(count, 3, r_unit.property_book_for or " ", format1_normal)


                # Fetch payment information from the associated contract
                contracts = self.env['contract.details'].search([('unit_id', '=', r_unit.id)])
                # payments = self.env['account.payment'].search([('unit_id', '=', r_unit.id)])
                if contracts and contracts.payment_ids:
                    row = count
                    for payment in contracts.payment_ids:
                        sheet.write(row, 4, payment.name or " ", format1_normal)
                        sheet.write(row, 5, payment.journal_id.name or " ", format1_normal)
                        sheet.write(row, 6, payment.amount_signed or " ", format1_normal)
                        sheet.write(row, 7, payment.date or " ", format1_normal)
                        sheet.write(row, 8, payment.state or " ", format1_normal)
                        row += 1
                    count = count + len(contracts.payment_ids)
                else:
                    count = count + 1
                sl_number = sl_number + 1


class UnitReport(models.TransientModel):
    _name = 'unit.report.wizard'

    property_id = fields.Many2one('product.product', string='Property')
    unit_ids = fields.Many2many('property.unit', string='Units')

    def print_units_report_xlsx(self):
        unit_domain = []
        unit_domain.append(('state', '=', 'reserve'))
        if self.property_id:
            unit_domain.append(('property_id', '=', self.property_id.id))
        if self.unit_ids:
            unit_domain.append(('id', 'in', self.unit_ids.ids))
        if unit_domain:
            units = self.env['property.unit'].search((unit_domain))

        if units:
            self.env.ref(
                'property_rental_mgt_app.reserve_units_report_xlsx').sudo().report_file = 'Units With Payment Data'

            data = {
                'ids': self.ids,
                'model': self._name,
                'form': {
                    'property_id': self.property_id.id,
                    'unit_ids': self.unit_ids.ids,
                },
            }

            return self.env.ref('property_rental_mgt_app.reserve_units_report_xlsx').report_action(self,data=data)

        else:
            raise ValidationError(
                _('No records found!!')
            )

    # code for button cancel
    def print_cancel(self):
        return {'type': 'ir.actions.act_window_close'}