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
from odoo import fields, models, api
from datetime import datetime, timedelta
import time


class LoyaltyConfiguration(models.TransientModel):
    _name = 'loyalty.config.settings'
    _inherit = 'res.config.settings'
    _description = 'Used to Store Loyalty Setting.'

    @api.model
    def load_loyalty_config_settings(self):
        record = {}
        settings_minimum_purchase = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'flexipharmacy.minimum_purchase')])
        if settings_minimum_purchase:
            record['minimum_purchase'] = float(settings_minimum_purchase.value)
        settings_points_based_on = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'flexipharmacy.points_based_on')])
        if settings_points_based_on:
            record['points_based_on'] = settings_points_based_on.value
        settings_point_calculation = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'flexipharmacy.point_calculation')])
        if settings_point_calculation:
            record['point_calculation'] = float(settings_point_calculation.value)
        settings_points = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'flexipharmacy.points')])
        if settings_points:
            record['points'] = float(settings_points.value)
        settings_to_amount = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'flexipharmacy.to_amount')])
        if settings_to_amount:
            record['to_amount'] = float(settings_to_amount.value)
        return [record]


    @api.model
    def get_values(self):
        res = super(LoyaltyConfiguration, self).get_values()
        param_obj = self.env['ir.config_parameter']
        res.update({
            'points_based_on': param_obj.sudo().get_param('flexipharmacy.points_based_on'),
            'minimum_purchase': float(param_obj.sudo().get_param('flexipharmacy.minimum_purchase')),
            'point_calculation': float(param_obj.sudo().get_param('flexipharmacy.point_calculation')),
            'points': int(param_obj.sudo().get_param('flexipharmacy.points')),
            'to_amount': float(param_obj.sudo().get_param('flexipharmacy.to_amount')),
        })
        return res

    @api.multi
    def set_values(self):
        res = super(LoyaltyConfiguration, self).set_values()
        param_obj = self.env['ir.config_parameter']
        param_obj.sudo().set_param('flexipharmacy.points_based_on', self.points_based_on)
        param_obj.sudo().set_param('flexipharmacy.minimum_purchase', float(self.minimum_purchase))
        param_obj.sudo().set_param('flexipharmacy.point_calculation', float(self.point_calculation))
        param_obj.sudo().set_param('flexipharmacy.points', int(self.points))
        param_obj.sudo().set_param('flexipharmacy.to_amount', float(self.to_amount))
        return res

    points_based_on = fields.Selection([('product', "Product"), ('order', "Order")],
                                       string="Points Based On",
                                       help='Loyalty points calculation can be based on products or order')
    minimum_purchase = fields.Float("Minimum Purchase")
    point_calculation = fields.Float("Point Calculation (%)")
    points = fields.Integer("Points")
    to_amount = fields.Float("To Amount")


class loyalty_point(models.Model):
    _name = "loyalty.point"
    _order = 'id desc'
    _rec_name = "pos_order_id"
    _description = 'Used to Store Loyalty Points.'

    pos_order_id = fields.Many2one("pos.order", string="Order", readonly=1)
    partner_id = fields.Many2one('res.partner', 'Member', readonly=1)
    amount_total = fields.Float('Total Amount', readonly=1)
    date = fields.Datetime('Date', readonly=1, default=datetime.now())
    points = fields.Float('Point', readonly=1)


class loyalty_point_redeem(models.Model):
    _name = "loyalty.point.redeem"
    _order = 'id desc'
    _rec_name = "redeemed_pos_order_id"
    _description = 'Used to Store Loyalty Redeem.'

    redeemed_pos_order_id = fields.Many2one("pos.order", string="Order")
    partner_id = fields.Many2one('res.partner', 'Member', readonly=1)
    redeemed_amount_total = fields.Float('Redeemed Amount', readonly=1)
    redeemed_date = fields.Datetime('Date', readonly=1, default=datetime.now())
    redeemed_point = fields.Float('Point', readonly=1)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
