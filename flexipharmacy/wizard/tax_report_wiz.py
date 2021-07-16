# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import xlwt
import io
import base64
from odoo.tools.misc import formatLang, format_date

class tax_rpeort_wiz(models.TransientModel):
    _name = "tax.report.wiz"
    _description = "Tax Report"

    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    data = fields.Binary(string="Data")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)

    def print_pdf(self, data):
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to'])[0]
        datas = {
            'ids': self._ids,
            'docs': self._ids,
            'model': 'tax.report.wiz',
            'form': data['form']
        }
        return self.env.ref('flexipharmacy.report_tax').report_action(self, data=datas)

    def print_xls(self):
        report_obj = self.env['report.flexipharmacy.tax_report_template']
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to'])[0]
        datas = {
            'ids': self._ids,
            'docs': self._ids,
            'model': 'tax.report.wiz',
            'form': data['form']
        }
        report_data = report_obj.with_context(active_model='tax.report.wiz')._get_report_values(self,data=datas)
        styleP = xlwt.XFStyle()
        stylePC = xlwt.XFStyle()
        styleBorder = xlwt.XFStyle()
        text_right = xlwt.XFStyle()
        fontbold = xlwt.XFStyle()
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment_right = xlwt.Alignment()
        alignment_right.horz = xlwt.Alignment.HORZ_RIGHT
        text_r = xlwt.Alignment()
        text_r.horz = xlwt.Alignment.HORZ_RIGHT
        stylePC.alignment =alignment_right
        font = xlwt.Font()
        fontP = xlwt.Font()
        text_right.font = fontP
        text_right.alignment = text_r
        borders = xlwt.Borders()
        borders.bottom = xlwt.Borders.THIN
        borders.top = xlwt.Borders.THIN
        borders.right = xlwt.Borders.THIN
        borders.left = xlwt.Borders.THIN
        font.bold = False
        fontP.bold = True
        styleP.font = font
        # stylePC.font = fontP
        stylePC.alignment = alignment_right
        styleBorder.font = fontP
        fontbold.font = fontP
        styleBorder.alignment = alignment
        styleBorder.borders = borders
        workbook = xlwt.Workbook(encoding="utf-8")
        worksheet = workbook.add_sheet("Tax Sheet")
        worksheet.col(0).width = 6000
        worksheet.col(1).width = 5600
        worksheet.col(2).width = 5600
        worksheet.write_merge(0, 2, 0, 2,
                              self.company_id.name + '\n' + self.company_id.email + '\n' + self.company_id.phone,
                              style=styleBorder)
        worksheet.write_merge(3, 3, 0, 2,'From ' + str(self.date_from) + ' To ' + str(self.date_to),styleBorder)
        worksheet.write_merge(4, 4, 0, 2, 'Tax Report', styleBorder)
        worksheet.write_merge(5, 5, 1, 1,'Net', text_right)
        worksheet.write_merge(5, 5, 2, 2, 'Tax', text_right)
        i = 6
        if report_data.get('taxes'):
            for each in report_data.get('taxes'):
                worksheet.write_merge(i, i, 0, 2,each,fontbold)
                i = i + 1
                if report_data.get('taxes').get(each):
                    for each in report_data.get('taxes')[each]:
                        worksheet.write_merge(i, i, 0, 0, each.get('name'))
                         
                        worksheet.write_merge(i, i, 1, 1, formatLang(self.env,float(each.get('base')),currency_obj=self.env.user.company_id.currency_id), stylePC)
                        worksheet.write_merge(i, i, 2, 2,formatLang(self.env,float(each.get('amount')),currency_obj=self.env.user.company_id.currency_id) , stylePC)
                        i = i + 1
        file_data = io.BytesIO()
        workbook.save(file_data)
        self.write({
            'state': 'get',
            'data': base64.encodestring(file_data.getvalue()),
            'name': 'tax_report.xls'
        })
        return {
            'name': 'Tax Report',
            'type': 'ir.actions.act_window',
            'res_model': 'tax.report.wiz',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }