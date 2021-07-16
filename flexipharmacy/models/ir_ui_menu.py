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
from odoo import SUPERUSER_ID


class ir_ui_menu(models.Model):
   _inherit = 'ir.ui.menu'

   @api.model
   def search(self, args, offset=0, limit=None, order=None, count=False):
       context = self._context or {}
       if args is None:
           args = []
       if self._uid != SUPERUSER_ID:
           # user_id = self.env['res.users'].search([('id', '=', self._uid)])
           if self.env.user.is_delivery_user == True:
               xml_id = self.env['ir.model.data'].get_object_reference('flexipharmacy', 'delivery_order_kanban_menu_id')
               # point_of_sale.menu_point_of_sale
               xml_id1 = self.env['ir.model.data'].get_object_reference('point_of_sale',
                                                                       'menu_point_of_sale')
               xml_id2 = self.env['ir.model.data'].get_object_reference('point_of_sale',
                                                                        'menu_point_root')
               if xml_id:
                   args += [('id', 'in', [xml_id[1], xml_id1[1], xml_id2[1]])]
       return super(ir_ui_menu, self).search(args, offset, limit, order, count=count)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: