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
from odoo.exceptions import UserError


class ValidDays(models.TransientModel):
    _name = "wizard.set.valid.days"

    product_category = fields.Many2many('pos.category', string="Product Category")
    products = fields.Many2many('product.product', string="Products",
                                domain="[('pos_categ_id', 'in', product_category)]")
    valid_days = fields.Integer(string="Valid Days", required=True)

    @api.multi
    def set_days(self):
        product = self.env['product.product']
        if self.product_category and self.products:
            product = product.search([('id', 'in', self.products.ids), ('pos_categ_id', 'in', self.product_category.ids)])
        elif self.product_category and not self.products:
            product = product.search([('pos_categ_id', 'in', self.product_category.ids)])
        elif self.products and not self.product_category:
            product = product.search([('id', 'in', self.products.ids)])
        else:
            raise UserError(_('Please Enter product category and products'))
        for each in product:
            each.return_valid_days = self.valid_days

    @api.onchange("product_category")
    def set_products(self):
        if self.product_category:
            return {'domain': {'products': [('pos_categ_id', 'in', self.product_category.ids)]}}
        else:
            return {'domain': {'products': [('id', 'in', self.env['product.product'].search([('available_in_pos','=',True)]).ids)]}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: