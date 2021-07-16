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

from odoo import models, fields, api, _
from odoo.tools.sql import drop_view_if_exists
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import Warning


class PosAgentCommission(models.Model):
    _name = 'pos.agent.commission'
    _description = 'Point of Sale Doctor Commission'

    agent_id = fields.Many2one('res.partner', string='Agent', required=True, domain="[('is_doctor', '=', True)]")
    name = fields.Char(string='Source Document', required=True)
    commission_date = fields.Date(string='Commission Date')
    amount = fields.Float(string='Amount')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('reserved', 'Reserved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft')
    invoice_id = fields.Many2one('account.invoice')
    commission_number = fields.Char(string='Number')
    order_id = fields.Many2one('pos.order')
    payment_id = fields.Many2one('pos.commission.payment')

    @api.model
    def create(self, vals):
        res =super(PosAgentCommission, self).create(vals)
        number = self.env['ir.sequence'].next_by_code('pos.agent.commission.number') or ''
        res.update({'commission_number': number})
        # vals['commission_number'] = self.env['ir.sequence'].next_by_code('pos.agent.commission.number')
        return res

    @api.multi
    def cancel_state(self):
        if self.state == 'draft':
            self.state = 'cancelled'


class PosCategoryCommission(models.Model):
    _name = 'pos.category.commission'
    _description = "Point of Sale Category Commission"

    agent_id = fields.Many2one('res.partner', string='Agent', domain="[('is_doctor', '=', True)]")
    calculation = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_price', 'Fixed Price')
    ], string='Calculation')
    commission = fields.Float(string='Commission')
    category_id = fields.Many2one('pos.category')


class PosProductCommission(models.Model):
    _name = 'pos.product.commission'
    _description = "Point of Sale Product Commission"

    agent_id = fields.Many2one('res.partner', string='Agent', domain="[('is_doctor', '=', True)]")
    calculation = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_price', 'Fixed Price')
    ], string='Calculation')
    commission = fields.Float(string='Commission')
    product_id = fields.Many2one('product.product')


class PosResPartnerCommission(models.Model):
    _name = 'pos.res.partner.commission'
    _description = "Point of Sale Doctor Commission"

    agent_id = fields.Many2one('res.partner', string='Agent', domain="[('is_doctor', '=', True)]")
    calculation = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_price', 'Fixed Price')
    ], string='Calculation')
    commission = fields.Float(string='Commission')
    partner_comm_id = fields.Many2one('res.partner')


class PosReportCommission(models.Model):
    _name = 'report.pos.commission'
    _auto = False
    _description = 'Commission Analysis'

    agent_id = fields.Many2one('res.partner', string='Agent', domain="[('is_doctor', '=', True)]")
    commission_date = fields.Date(string='Commission Date')
    amount = fields.Float(string='Amount')

    @api.model_cr
    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
                    create or replace view report_pos_commission as (
                        select * from pos_agent_commission
                    )
                """)


class PosCommissionPayment(models.Model):
    _name = 'pos.commission.payment'
    _description = "Point of Sale Commission Payment"

    agent_id = fields.Many2one('res.partner', string='Agent', domain="[('is_doctor', '=', True)]", required=True)
    commission_pay_ids = fields.One2many('pos.agent.commission', 'payment_id', string='Commission Payment')

    @api.onchange('agent_id')
    def _onchange_agent(self):
        data_filter = [('agent_id', '=', self.agent_id.id), ('state', '=', 'draft')]
        payment_browse = self.env['pos.agent.commission'].search(data_filter)
        self.commission_pay_ids = [(6, 0, payment_browse.ids)]

    @api.multi
    def payment(self):
        IrDefault = self.env['ir.default'].sudo()
        # account_id = IrDefault.get('res.config.settings', "pos_account_id")
        account_id = int(self.env['ir.config_parameter'].sudo().get_param('pos_account_id')) \
            if self.env['ir.config_parameter'].sudo().get_param('pos_account_id') else False
        if not account_id:
            raise Warning(_(
                'Commission Account is not Found. Please go to Invoice Configuration and set the Commission account.'))
        else:
            account_id = self.env['account.account'].search([('id', '=', account_id)])
            if not account_id:
                raise Warning(_(
                    'Commission Account is not Found. Please go to Invoice Configuration and set the Commission account.'))
        agent_detail = {'partner_id': self.agent_id.id,
                        'date_invoice': date.today(),
                        'type': 'in_invoice'}
        invoice_line_data = []
        i = 1 if self.agent_id.pos_commission_payment_type == 'monthly' \
            else 3 if self.agent_id.pos_commission_payment_type == 'quarterly' \
            else 6 if self.agent_id.pos_commission_payment_type == 'biyearly' \
            else 12
        self.agent_id.pos_next_payment_date = date.today() + relativedelta(months=i)
        total_amount = 0
        for each in self.commission_pay_ids:
            total_amount += each.amount
            each.write({'state': 'reserved'})
            invoice_line_data.append((0, 0, {'account_id': account_id.id,
                                             'name': each.commission_number + " Doctor Commission",
                                             'quantity': 1,
                                             'price_unit': each.amount,
                                         }
                                  ))
        agent_detail.update({'invoice_line_ids': invoice_line_data,
                             'pos_vendor_commission_ids': [(6, 0, self.commission_pay_ids.ids)]
                             })
        invoice_id = self.env['account.invoice'].create(agent_detail)
        invoice_id.action_invoice_open()
        journal_id = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)

        amount = total_amount * self.agent_id.currency_id._get_conversion_rate(
            from_currency=invoice_id.currency_id,
            to_currency=self.agent_id.currency_id, company=self.env.user.company_id, date=date.today())
        payment_id = self.env['account.payment'].create({'invoice_ids': [(4, invoice_id.id)],
                                                         'payment_type': 'outbound',
                                                         'partner_type': 'supplier',
                                                         'partner_id': self.agent_id.id,
                                                         'amount': amount,
                                                         'journal_id': journal_id.id,
                                                         'payment_date': date.today(),
                                                         'payment_method_id': '1',
                                                         'account_id': account_id.id,
                                                         'communication': invoice_id.number,
                                                         'currency_id': self.agent_id.currency_id.id})
        payment_id.post()
        for each in invoice_id.pos_vendor_commission_ids:
            if each.state == 'reserved':
                each.state = 'paid'
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
