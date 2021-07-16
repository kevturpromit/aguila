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

from odoo import api, models, fields


class SaleProductConfigurator(models.TransientModel):
    _name = 'pos.pending.payment.report'
    _description = 'Pos Pending Payment Report Wizard'

    with_detail = fields.Boolean('With Details')

    @api.multi
    def generate_report(self):
        data = {'with_detail': self.with_detail}
        return self.env.ref('flexipharmacy.action_pos_pending_payment_report').report_action([], data=data)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: