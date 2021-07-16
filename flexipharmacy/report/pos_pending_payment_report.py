# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import api, fields, models


class pos_unpaid_report(models.AbstractModel):
    _name = 'report.flexipharmacy.report_pos_pending_payment'
    _description = 'POS Pending Payment Report'

    @api.multi
    def get_statement(self, obj):
        self._cr.execute("""
                    SELECT 
                        absl.amount AS amount_paid,
                        absl.date AS date_order,
                        aj.name AS journal_id
                    FROM 
                        account_bank_statement_line as absl 
                    INNER JOIN account_journal AS aj ON aj.id = absl.journal_id
                    WHERE pos_statement_id={0}
                    GROUP BY
                        absl.amount, absl.date, aj.name""".format(obj.get('id')))
        statement = self._cr.dictfetchall()
        return statement

    @api.multi
    def _get_report_values(self, docids, data=None):
        self._cr.execute("""
                    SELECT
                        po.id as id,
                        rp.name as partner_id,
                        po.date_order,
                        po.name as order_name,
                        po.amount_total,
                        po.amount_paid,
                        (po.amount_total - po.amount_paid) AS amount_due
                        FROM pos_order AS po
                        INNER JOIN res_partner AS rp ON rp.id = po.partner_id
                        WHERE po.state = 'draft'
                        GROUP BY po.amount_total, po.amount_paid, rp.name, 
                        po.date_order, po.name, po.id
                        ORDER BY partner_id, order_name
                        """)
        result = self._cr.dictfetchall()
        main_dict = {}
        for each in result:
            if each.get('partner_id') in main_dict:
                test = main_dict.get(each.get('partner_id')) or []
                test.append(each)
                main_dict[each.get('partner_id')] = test
            else:
                main_dict[each.get('partner_id')] = [each]
        return {
            'docs': main_dict,
            'get_statement': self.get_statement,
            'symbol': self.env.user.company_id.currency_id.symbol,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
