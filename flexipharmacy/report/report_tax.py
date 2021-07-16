# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime


class report_tax(models.AbstractModel):
    _name = 'report.flexipharmacy.tax_report_template'
    _description = 'Report Tax'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        account_result = {}
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account') 
        accounts = self.env['account.account'].search([])
        date_from = data.get('form') and data.get('form').get('date_from')
        date_to = data.get('form') and data.get('form').get('date_to')
        where_clause = ""
        SQL = """ 
            SELECT 
              ait.tax_id as tax_id, 
              ait.base as base, 
              ait.amount as amount,
              at.name as name,
              at.type_tax_use as type 
            FROM 
              account_move_line as aml,
              account_move as am,
              account_move_line_account_tax_rel as tax_rel,
              account_invoice_tax as ait,
              account_invoice as ai,
              account_tax as at
            WHERE 
              aml.move_id = am.id AND
              aml.invoice_id = ai.id AND
              aml.id = tax_rel.account_move_line_id AND
              ait.invoice_id = ai.id AND
              ait.tax_id = at.id AND 
              at.type_tax_use in ('sale', 'purchase') AND
              am.state = 'posted'
        """

        if date_from:
            where_clause += "AND am.date >= '%s' "% (date_from)
        if date_to:
            where_clause += "AND am.date <= '%s' "% (date_to)
        self.env.cr.execute(SQL + where_clause)
        res = self.env.cr.dictfetchall()
        groups = dict((tp, []) for tp in ['sale', 'purchase'])
        for row in res:
            tax_id = self.env['account.tax'].browse(row['tax_id'])
            if row['tax_id'] in list(account_result.keys()):
                account_result[row['tax_id']]['base'] += row.get('base')
                account_result[row['tax_id']]['amount'] += row.get('amount')
            else:
                account_result[row.pop('tax_id')] = row
        for each in account_result.values():
            groups[each['type']].append(each)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data,
            'docs': docs,
            'taxes': groups,
        }
