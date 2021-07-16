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

import json

from odoo import http
from odoo.http import request
from odoo.tools.translate import _
import werkzeug.utils
import hashlib
from odoo import http
import json
from odoo.addons.web.controllers.main import Home, ensure_db
from odoo.addons.bus.controllers.main import BusController

import logging

_logger = logging.getLogger(__name__)


class PosSpeedControl(BusController):
    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            channels = list(channels)
            channels.append((request.db, 'change_detector'))
        return super(PosSpeedControl, self)._poll(dbname, channels, last, options)


class Home(Home):
    @http.route('/web/login', type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        res = super(Home, self).web_login(redirect, **kw)
        if request.params['login_success']:
            uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            users = request.env['res.users'].browse([uid])
            if users.login_with_pos_screen:
                pos_session = request.env['pos.session'].sudo().search(
                    [('config_id', '=', users.default_pos.id), ('state', '=', 'opened')])
                if pos_session:
                    return http.redirect_with_hash('/pos/web')
                else:
                    session_id = users.default_pos.open_session_cb()
                    pos_session = request.env['pos.session'].sudo().search(
                        [('config_id', '=', users.default_pos.id), ('state', '=', 'opening_control')])
                    if users.default_pos.cash_control:
                        pos_session.write({'opening_balance': True})
                    session_open = pos_session.action_pos_session_open()
                    return http.redirect_with_hash('/pos/web')
            else:
                return res
        else:
            return res


class DataSet(http.Controller):

    @http.route('/web/dataset/get_country', type='http', auth="user")
    def get_country(self, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        county_code = kw.get('country_code')
        country_obj = request.env['res.country']
        country_id = country_obj.search([('code', '=', county_code)])
        if country_id:
            # return json.dumps(country_id.read())
            data = country_id.read()
            data[0].pop('create_date')
            data[0].pop('__last_update')
            data[0].pop('write_date')
            data[0]['image'] = False
            return json.dumps(data)
        else:
            return False

    # load background
#     @http.route('/web/dataset/load_products', type='http', auth="user")
#     def load_products(self, **kw):
#         cr, uid, context = request.cr, request.uid, request.context
#         product_ids = eval(kw.get('product_ids'))
#         fields = eval(kw.get('fields'))
#         stock_location_id = eval(kw.get('stock_location_id'))
#         if product_ids and fields:
#             # records = request.env['product.product'].search_read([('id', 'in', product_ids)], fields)
#             records = request.env['product.product'].with_context(
#                         {'location': stock_location_id, 'compute_child': False}).search_read([('id', 'in', product_ids)],fields)
#             if records:
#                 for each_rec in records:
#                     new_date = each_rec['write_date']
#                     each_rec['write_date'] = new_date.strftime('%Y-%m-%d %H:%M:%S')
#                 return json.dumps(records)
#         return json.dumps([])

    @http.route('/web/dataset/load_products', type='http', auth="user", methods=['POST'], csrf=False)
    def load_products(self, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        product_ids = eval(kw.get('product_ids'))
        fields = eval(kw.get('fields'))
        stock_location_id = eval(kw.get('stock_location_id'))
        if product_ids and fields:
            records = request.env['product.product'].with_context({'location' : stock_location_id, 'compute_child': False}).search_read([('id', 'in', product_ids)], fields)
            template_ids = []
            if records:
                for each_rec in records:
                    template_ids.append(each_rec['product_tmpl_id'][0])
                    new_date = each_rec['write_date']
                    each_rec['write_date'] = new_date.strftime('%Y-%m-%d %H:%M:%S')

                template_fields = fields + ['name', 'display_name', 'product_variant_ids','product_variant_count']
                template_ids = list(dict.fromkeys(template_ids))
                product_temp_ids = request.env['product.template'].with_context({'location' : stock_location_id, 'compute_child': False}).search_read([('id', 'in', template_ids)], template_fields)
                for each_temp in product_temp_ids:
                    temp_new_date = each_temp['write_date']
                    each_temp['write_date'] = temp_new_date.strftime('%Y-%m-%d %H:%M:%S')
                return json.dumps({'templates':product_temp_ids,'product':records})
        return json.dumps([])

    @http.route('/web/dataset/load_products_template', type='http', auth="user", methods=['POST'], csrf=False)
    def load_products_template(self, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        product_ids = eval(kw.get('product_ids'))
        product_ids = list(dict.fromkeys(product_ids))
        fields = eval(kw.get('fields'))
        stock_location_id = eval(kw.get('stock_location_id'))
        if product_ids and fields:
            records = request.env['product.template'].with_context({'location' : stock_location_id, 'compute_child': False}).search_read([('id', 'in', product_ids)], fields)
            template_ids = []
            if records:
                for each_rec in records:
                    new_date = each_rec['write_date']
                    each_rec['write_date'] = new_date.strftime('%Y-%m-%d %H:%M:%S')
                return json.dumps(records)
        return json.dumps([])

    @http.route('/web/dataset/load_cache_with_template', type='http', auth="user", methods=['POST'], csrf=False)
    def get_products_from_cache(self, **kw):
        config = request.env['pos.config'].browse(int(kw.get('config_id')))
        domain = [["sale_ok", "=", True], ["available_in_pos", "=", True]]
        fields = eval(kw.get('fields'))
        cache_for_user = config._get_cache_for_user()
        if cache_for_user:
            cache_records = cache_for_user.get_cache(domain, fields) or []
            return json.dumps(cache_records)
        else:
            pos_cache = request.env['pos.cache']
            pos_cache.create({
                'config_id': config.id,
                'product_domain': str(domain),
                'product_fields': str(fields),
                'compute_user_id': request.env.uid
            })
            new_cache = config._get_cache_for_user()
            return json.dumps(new_cache.get_cache(domain, fields) or [])

    # Store data to cache
    @http.route('/web/dataset/store_data_to_cache', type='http', auth="user", methods=['POST'], csrf=False)
    def store_data_to_cache(self, **kw):
        cache_data = json.loads(kw.get('cache_data'))
        result = request.env['pos.config'].store_data_to_cache(cache_data, [])
        return json.dumps([])

    # Load Customers
    @http.route('/web/dataset/load_customers', type='http', auth="user", methods=['POST'], csrf=False)
    def load_customers(self, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        partner_ids = eval(kw.get('partner_ids'))
        records = []
        fields = []
        if eval(kw.get('fields')):
            fields = eval(kw.get('fields'))
        domain = [('id', 'in', partner_ids), ('customer', '=', True)]
        try:
            records = request.env['res.partner'].search_read(domain, fields)
            if records:
                for each_rec in records:
                    if each_rec['birth_date']:
                        client_birth_date = each_rec['birth_date']
                        each_rec['birth_date'] = client_birth_date.strftime('%Y-%m-%d')
                    if each_rec['anniversary_date']:
                        client_anniversary_date = each_rec['anniversary_date']
                        each_rec['anniversary_date'] = client_anniversary_date.strftime('%Y-%m-%d')
                    if each_rec['write_date']:
                        client_write_date = each_rec['write_date']
                        each_rec['write_date'] = client_write_date.strftime('%Y-%m-%d %H:%M:%S')
                return json.dumps(records)
        except Exception as e:
            print ("\n Error......", e)
        return json.dumps([])

#     @http.route('/web/dataset/get_update', type='http', auth="user")
#     def get_update(self, **kw):
#         cr, uid, context = request.cr, request.uid, request.context
#         sess_id = int(kw.get('check_session_id'))
#         if(kw.get('get_message')):
#             if sess_id :
#                 session_notify_message_data = request.env['message.terminal'].search([('message_session_id', '=',sess_id)],order="id desc",limit=1)
#                 if session_notify_message_data:
#                     return json.dumps(session_notify_message_data.read())
#         else:
#             cash_id = int(kw.get('current_cashier'))
#             cash_name = kw.get('cashier_name')
#             if sess_id and cash_id :
#                 session_notify_data = request.env['lock.data'].search([('session_id','=',sess_id),('locked_user_id', '=',cash_id)])
#                 if session_notify_data:
#                     return json.dumps(session_notify_data.read())
#         return []

class TerminalLockController(BusController):

    def _poll(self, dbname, channels, last, options):
        """Add the relevant channels to the BusController polling."""
        if options.get('customer.display'):
            channels = list(channels)
            ticket_channel = (
                request.db,
                'customer.display',
                options.get('customer.display')
            )
            channels.append(ticket_channel)

        if options.get('lock.data'):
            channels = list(channels)
            lock_channel = (
                request.db,
                'lock.data',
                options.get('lock.data')
            )
            channels.append(lock_channel)
        return super(TerminalLockController, self)._poll(dbname, channels, last, options)


# class CustomerDisplayController(BusController):
#
#     def _poll(self, dbname, channels, last, options):
#         """Add the relevant channels to the BusController polling."""
#         if options.get('customer.display'):
#             channels = list(channels)
#             ticket_channel = (
#                 request.db,
#                 'customer.display',
#                 options.get('customer.display')
#             )
#             channels.append(ticket_channel)
#         return super(CustomerDisplayController, self)._poll(dbname, channels, last, options)


class PosMirrorController(http.Controller):

    @http.route('/web/customer_display', type='http', auth='user')
    def white_board_web(self, **k):
        config_id = False
        pos_sessions = request.env['pos.session'].search([
            ('state', '=', 'opened'),
            ('user_id', '=', request.session.uid),
            ('rescue', '=', False)])
        if pos_sessions:
            config_id = pos_sessions.config_id.id
        context = {
            'session_info': json.dumps(request.env['ir.http'].session_info()),
            'config_id': config_id,
        }
        return request.render('flexipharmacy.customer_display_index', qcontext=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
