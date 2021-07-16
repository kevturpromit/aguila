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

import ast
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        res_user_ids = param_obj.sudo().get_param('res_user_ids')
        if res_user_ids:
            res.update({'res_user_ids': ast.literal_eval(res_user_ids)})

        res.update(
            google_api_key=param_obj.get_param('google_api_key'),
            theme_selector=param_obj.get_param('theme_selector'),
            gen_barcode=param_obj.get_param('gen_barcode'),
            barcode_selection=param_obj.get_param('barcode_selection'),
            gen_internal_ref=param_obj.get_param('gen_internal_ref'),
            mailsend_check=param_obj.get_param('mailsend_check'),
            email_notification_days=int(param_obj.sudo().get_param('email_notification_days')),
            bday_tmpl_id=int(param_obj.sudo().get_param('bday_tmpl_id'))
                            if param_obj.sudo().get_param('bday_tmpl_id') else False,
            anniversary_tmpl_id=int(param_obj.sudo().get_param('anniversary_tmpl_id'))
                            if param_obj.sudo().get_param('anniversary_tmpl_id') else False,
            is_rfid_login=param_obj.get_param('is_rfid_login'),
            #Commission Part
            pos_commission_calculation=param_obj.get_param('flexipharmacy.pos_commission_calculation'),
            pos_commission_based_on=param_obj.get_param('flexipharmacy.pos_commission_based_on'),
            pos_commission_with=param_obj.get_param('flexipharmacy.pos_commission_with'),
            is_pos_agent_commission=param_obj.get_param('flexipharmacy.is_pos_agent_commission'),
            pos_account_id=int(param_obj.sudo().get_param('pos_account_id'))
                            if param_obj.sudo().get_param('pos_account_id') else False,
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_param('google_api_key', self.google_api_key or '')
        param_obj.set_param('theme_selector', self.theme_selector or False)
        param_obj.set_param('gen_barcode', self.gen_barcode)
        param_obj.set_param('barcode_selection', self.barcode_selection)
        param_obj.set_param('gen_internal_ref', self.gen_internal_ref)
        param_obj.sudo().set_param('mailsend_check', self.mailsend_check)
        param_obj.sudo().set_param('res_user_ids', self.res_user_ids.ids)
        param_obj.sudo().set_param('email_notification_days', self.email_notification_days)
        param_obj.set_param('bday_tmpl_id',self.bday_tmpl_id and self.bday_tmpl_id.id or False)
        param_obj.set_param('anniversary_tmpl_id',self.anniversary_tmpl_id and self.anniversary_tmpl_id.id or False)
        param_obj.set_param('is_rfid_login', self.is_rfid_login or False)
        #Commission Part
        param_obj.set_param("flexipharmacy.pos_commission_calculation", self.pos_commission_calculation)
        param_obj.set_param("flexipharmacy.pos_commission_based_on", self.pos_commission_based_on)
        param_obj.set_param("flexipharmacy.pos_commission_with", self.pos_commission_with)
        param_obj.set_param("flexipharmacy.is_pos_agent_commission", self.is_pos_agent_commission)
        param_obj.set_param('pos_account_id',self.pos_account_id and self.pos_account_id.id or False)
        return res

    google_api_key = fields.Char('Google API key')
    theme_selector = fields.Selection([('blue-green', 'Blue Green'), ('purple-pink', 'Purple Pink'),
                                       ('orange-green', 'Orange Green')])
    gen_barcode = fields.Boolean("On Product Create Generate Barcode")
    barcode_selection = fields.Selection([('code_39', 'CODE 39'), ('code_128', 'CODE 128'),
                                          ('ean_13', 'EAN-13'), ('ean_8', 'EAN-8'),
                                          ('isbn_13', 'ISBN 13'), ('isbn_10', 'ISBN 10'),
                                          ('issn', 'ISSN'), ('upca', 'UPC-A')], string="Select Barcode Type")
    gen_internal_ref = fields.Boolean(string="On Product Create Generate Internal Reference")
    mailsend_check = fields.Boolean(string="Send Mail")
    email_notification_days = fields.Integer(string="Expiry Alert Days")
    res_user_ids = fields.Many2many('res.users', string='Users')
    bday_tmpl_id = fields.Many2one('mail.template', string="Birthday Template",
                                   domain="[('model', '=','res.partner')]")
    anniversary_tmpl_id = fields.Many2one('mail.template', string="Anniversary Template",
                                          domain="[('model', '=','res.partner')]")
    is_rfid_login = fields.Boolean("RFID Pos Login")
    #Doctor Commission Fields
    pos_commission_calculation = fields.Selection([
        ('product', 'Product'),
        ('product_category', 'Product Category'),
        ('agent', 'Doctor'),
    ], string='Commission Calculation ')
    pos_account_id = fields.Many2one('account.account', string='Commission Account ')
    pos_commission_based_on = fields.Selection([
        ('product_sell_price', 'Product Sell Price'),
        ('product_profit_margin', 'Product Profit Margin')
    ], string='Commission Based On ')
    pos_commission_with = fields.Selection([
        ('with_tax', 'Tax Included'),
        ('without_tax', 'Tax Excluded')
    ], string='Apply Commission With ')
    is_pos_agent_commission = fields.Boolean(string='Doctor Commission ')


class res_company(models.Model):
    _inherit = "res.company"

    pos_price = fields.Char(string="Pos Price", size=1)
    pos_quantity = fields.Char(string="Pos Quantity", size=1)
    pos_discount = fields.Char(string="Pos Discount", size=1)
    pos_search = fields.Char(string="Pos Search", size=1)
    pos_next = fields.Char(string="Pos Next order", size=1)
    payment_total = fields.Char(string="Payment", size=1)
    report_ip_address = fields.Char(string="Thermal Printer Proxy IP")
    shop_ids = fields.Many2many("pos.shop", 'pos_shop_company_rel', 'shop_id', 'company_id', string='Allow Shops')

    @api.one
    def write(self, vals):
        current_shop_ids = self.shop_ids
        res = super(res_company, self).write(vals)
        if 'shop_ids' in vals:
            current_shop_ids -= self.shop_ids
            for shop in current_shop_ids:
                shop.company_id = False
            for shop in self.shop_ids:
                shop.company_id = self
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
