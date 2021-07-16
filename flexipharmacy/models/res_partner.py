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
from datetime import datetime, date
import logging
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def calculate_partner(self):
        partner_ids = self.search(
            [('customer', '=', True)])
        if partner_ids:
            return partner_ids.ids
        else:
            return []

    @api.model
    def customer_greetings(self):
        today = date.today()
        partner = self.search([('customer', '=', True), ('email', "!=", False)])
        birthday_tmpl = self.env['ir.config_parameter'].sudo().get_param('bday_tmpl_id')
        anniversary_tmpl = self.env['ir.config_parameter'].sudo().get_param('anniversary_tmpl_id')

        if partner:
            for each in partner:
                if each.birth_date == today:
                    try:
                        template_obj = self.env['mail.template'].browse(int(birthday_tmpl))
                        template_obj.send_mail(each.id, force_send=True, raise_exception=False)

                    except Exception as e:
                        _logger.error('Unable to send email for birthday %s', e)

                if each.anniversary_date == today:
                    try:
                        template_obj = self.env['mail.template'].browse(int(anniversary_tmpl))

                        template_obj.send_mail(each.id, force_send=True, raise_exception=False)

                    except Exception as e:
                        _logger.error('Unable to send email for anniversary %s', e)

    @api.model
    def create_from_ui(self, partner):
        if partner.get('property_product_pricelist'):
            price_list_id = int(partner.get('property_product_pricelist'))
            partner.update({'property_product_pricelist': price_list_id})
        return super(ResPartner, self).create_from_ui(partner)

    @api.model
    def loyalty_reminder(self):
        partner_ids = self.search([('email', "!=", False), ('send_loyalty_mail', '=', True)])
        for partner_id in partner_ids.filtered(lambda partner: partner.remaining_loyalty_points > 0):
            try:
                template_id = self.env['ir.model.data'].get_object_reference('flexipharmacy',
                                                                             'email_template_loyalty_reminder')
                template_obj = self.env['mail.template'].browse(template_id[1])
                template_obj.send_mail(partner_id.id, force_send=True, raise_exception=False)
            except Exception as e:
                _logger.error('Unable to send email for order %s', e)

    @api.multi
    def _calculate_earned_loyalty_points(self):
        loyalty_point_obj = self.env['loyalty.point']
        for partner in self:
            total_earned_points = 0.00
            for earned_loyalty in loyalty_point_obj.search([('partner_id', '=', partner.id)]):
                total_earned_points += earned_loyalty.points
            partner.loyalty_points_earned = total_earned_points

    @api.multi
    def _calculate_remaining_loyalty(self):
        loyalty_point_obj = self.env['loyalty.point']
        loyalty_point_redeem_obj = self.env['loyalty.point.redeem']
        for partner in self:
            points_earned = 0.00
            amount_earned = 0.00
            points_redeemed = 0.00
            amount_redeemed = 0.00
            for earned_loyalty in loyalty_point_obj.search([('partner_id', '=', partner.id)]):
                points_earned += earned_loyalty.points
                amount_earned += earned_loyalty.amount_total
            for redeemed_loyalty in loyalty_point_redeem_obj.search([('partner_id', '=', partner.id)]):
                points_redeemed += redeemed_loyalty.redeemed_point
                amount_redeemed += redeemed_loyalty.redeemed_amount_total
            partner.remaining_loyalty_points = points_earned - points_redeemed
            partner.remaining_loyalty_amount = amount_earned - amount_redeemed
            # partner.sudo().write({
            #     'total_remaining_points': points_earned - points_redeemed
            # })
            partner.total_remaining_points = points_earned - points_redeemed

    @api.multi
    def _compute_remain_credit_limit(self):
        for partner in self:
            total_credited = 0
            orders = self.env['pos.order'].search([('partner_id', '=', partner.id),
                                                   ('state', '=', 'draft')])
            for order in orders:
                total_credited += order.amount_due
            partner.remaining_credit_limit = partner.credit_limit - total_credited

    @api.multi
    @api.depends('used_ids', 'recharged_ids')
    def compute_amount(self):
        total_amount = 0
        for ids in self:
            for card_id in ids.card_ids:
                total_amount += card_id.card_value
            ids.remaining_amount = total_amount

    @api.one
    @api.depends('wallet_lines')
    def _calc_remaining(self):
        total = 0.00
        for s in self:
            for line in s.wallet_lines:
                total += line.credit - line.debit
        self.remaining_wallet_amount = total

    @api.multi
    def _calc_credit_remaining(self):
        for partner in self:
            data = self.env['account.invoice'].get_outstanding_info(partner.id)
            amount = []
            amount_data = 0.00
            total = 0.00
            for pay in data['content']:
                amount_data = pay['amount']
                amount.append(amount_data)
            for each_amount in amount:
                total += each_amount
            partner.remaining_credit_amount = total

    @api.multi
    def _calc_debit_remaining(self):
        for partner in self:
            pos_orders = self.env['pos.order'].search([('partner_id', '=', partner.id), ('state', '=', 'draft')
                                                          , ('reserved', '=', False)])
            amount = sum([order.amount_due for order in pos_orders]) or 0.00
            partner.remaining_debit_amount = partner.debit_limit - amount

    @api.constrains('pos_agent_commission_ids', 'pos_agent_commission_ids.commission')
    def _check_commission_values(self):
        if self.pos_agent_commission_ids.filtered(
                lambda line: line.calculation == 'percentage' and line.commission > 100 or line.commission < 0.0):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    @api.constrains('is_doctor')
    def check_vendor(self):
        if self.is_doctor and not self.supplier:
            raise Warning(_('Supplier Must be Doctor.'))

    @api.multi
    def pos_payment_cron(self):
        account_id = int(self.env['ir.config_parameter'].sudo().get_param('pos_account_id')) \
                        if self.env['ir.config_parameter'].sudo().get_param('pos_account_id') else False
        if account_id:
            account_id = self.env['account.account'].search([('id', '=', account_id)])
            agent_browse = self.search([('is_doctor', '=', True),
                                        ('pos_commission_payment_type', '!=', 'manually')])
            for agent in agent_browse:
                commission_browse = self.env['pos.agent.commission'].search([('state', '=', 'draft'),
                                                                         ('agent_id', '=', agent.id)])
                if agent.pos_next_payment_date == date.today() or not agent.pos_next_payment_date:
                    total_amount = 0
                    agent_detail = {'partner_id': agent.id,
                                    'date_invoice': date.today(),
                                    'type': 'in_invoice', }
                    vendor_commission_list, invoice_line_data = [], []
                    for commission in commission_browse:
                        total_amount += commission.amount
                        i = 1 if agent.pos_commission_payment_type == 'monthly' \
                            else 3 if agent.pos_commission_payment_type == 'quarterly' \
                            else 6 if agent.pos_commission_payment_type == 'biyearly' \
                            else 12
                        agent.pos_next_payment_date = date.today() + relativedelta(months=i)
                        commission.write({'state': 'reserved'})
                        vendor_commission_list.append(commission.id)
                        invoice_line_data.append((0, 0, {'account_id': account_id.id,
                                                         'name': commission.commission_number + " Doctor Commission",
                                                         'quantity': 1,
                                                         'price_unit': commission.amount,
                                                         }
                                                  ))
                        agent_detail.update({'invoice_line_ids': invoice_line_data,
                                             'pos_vendor_commission_ids': [(6, 0, vendor_commission_list)]
                                             })
                    invoice_id = self.env['account.invoice'].create(agent_detail)
                    invoice_id.action_invoice_open()
                    journal_id = self.env['account.journal'].search(
                        [('type', '=', 'bank')], limit=1)

                    amount = total_amount * agent.currency_id._get_conversion_rate(
                        from_currency=invoice_id.currency_id,
                        to_currency=agent.currency_id, company=self.env.user.company_id, date=date.today())

                    payment_id = self.env['account.payment'].create({'invoice_ids': [(4, invoice_id.id)],
                                                                     'payment_type': 'outbound',
                                                                     'partner_type': 'supplier',
                                                                     'partner_id': agent.id,
                                                                     'amount': amount,
                                                                     'journal_id': journal_id.id,
                                                                     'payment_date': date.today(),
                                                                     'payment_method_id': '1',
                                                                     'account_id': account_id.id,
                                                                     'communication': invoice_id.number})
                    payment_id.post()
                    for each in invoice_id.pos_vendor_commission_ids:
                        if each.state == 'reserved':
                            each.state = 'paid'

    @api.multi
    def _pos_compute_commission(self):
        commission = self.env['pos.agent.commission'].search([])
        for customer in self:
            for each in commission:
                if each.agent_id.id == customer.id:
                    customer.pos_commission_count += each.amount

    @api.multi
    def pos_commission_payment_count(self):
        return {
            'name': _('PoS Doctor Commission'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'pos.agent.commission',
            'view_id': False,
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [('agent_id', 'in', [self.id])],
        }

    card_ids = fields.One2many('aspl.gift.card', 'customer_id', string="List of card")
    used_ids = fields.One2many('aspl.gift.card.use', 'customer_id', string="List of used card")
    recharged_ids = fields.One2many('aspl.gift.card.recharge', 'customer_id', string="List of recharged card")
    remaining_amount = fields.Char(compute=compute_amount, string="Remaining Giftcard Amount", readonly=True)

    wallet_lines = fields.One2many('wallet.management', 'customer_id', string="Wallet", readonly=True)
    remaining_wallet_amount = fields.Float(compute="_calc_remaining", string="Remaining Amount", readonly=True)
    prefer_ereceipt = fields.Boolean('Prefer E-Receipt')
    remaining_credit_limit = fields.Float("Remaining Reservation Credit Limit", compute="_compute_remain_credit_limit")
    loyalty_points_earned = fields.Float(compute='_calculate_earned_loyalty_points')
    remaining_loyalty_points = fields.Float("Remaining Loyalty Points", readonly=1,
                                            compute='_calculate_remaining_loyalty')
    remaining_loyalty_amount = fields.Float("Points to Amount", readonly=1, compute='_calculate_remaining_loyalty')
    send_loyalty_mail = fields.Boolean("Send Loyalty Mail", default=True)
    total_remaining_points = fields.Float("Total Loyalty Points", readonly=1)
    # Credit Management
    remaining_credit_amount = fields.Float(compute="_calc_credit_remaining", string="Remaining Amount",
                                           store=True, readonly=True)
    # Debit Management
    debit_limit = fields.Float("Debit Limit")
    remaining_debit_amount = fields.Float(compute="_calc_debit_remaining", string="Remaining Debit Limit",
                                          readonly=True)
    exchange_history_ids = fields.One2many('aspl.gift.card.exchange.history', 'customer_id')
    birth_date = fields.Date("Birth Date")
    anniversary_date = fields.Date("Anniversary Date")
    is_doctor = fields.Boolean(string="Doctor")
    #Commission Part
#     is_pos_agent = fields.Boolean(string='Agent ')
    pos_agent_commission_ids = fields.One2many('pos.res.partner.commission', 'partner_comm_id', string="Doctor Commission")
    pos_commission_payment_type = fields.Selection([
                                                    ('manually', 'Manually'),
                                                    ('monthly', 'Monthly'),
                                                    ('quarterly', 'Quarterly'),
                                                    ('biyearly', 'Biyearly'),
                                                    ('yearly', 'Yearly')
                                                    ], string='Commission Payment Type ')
    pos_next_payment_date = fields.Date(string='Next Payment Date ', readonly=True, store=True)
    pos_commission_count = fields.Float(string='PoS Commission', compute='_pos_compute_commission')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
