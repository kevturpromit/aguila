# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime


class report_trial_balance(models.AbstractModel):
    _name = 'report.flexipharmacy.trial_balance_template'
    _description = 'report_trial_balance'

    def _get_init_bal(self, from_date, company_id, account_id):
        if from_date and company_id and account_id:
            account_config_id = self.env['res.config.settings'].search([], order='id desc', limit=1)
            current_year = datetime.strptime(from_date, '%Y-%m-%d').year
            fiscal_year_start_date = ''
            if account_config_id and account_config_id.fiscalyear_last_month and account_config_id.fiscalyear_last_day:
                fiscal_month = account_config_id.fiscalyear_last_month
                fiscal_end_date = account_config_id.fiscalyear_last_day
                if fiscal_month == 12:
                    current_year -= 1
                fiscal_year_start_date = str(current_year) + '-' + str(fiscal_month) + '-' + str(fiscal_end_date)
                fiscal_year_start_date = datetime.strftime(datetime.strptime(fiscal_year_start_date, '%Y-%m-%d') + timedelta(days=1), '%Y-%m-%d')
            else:
                fiscal_year_start_date = str(current_year) + '-01-01'
            SQL = """select sum(aml.debit) as debit, sum(aml.credit) as credit
                    FROM account_move_line aml,account_move am
                    WHERE 
                    aml.move_id = am.id AND
                    aml.account_id = %s
                    AND aml.company_id = %s
                    AND aml.date::timestamp::date < '%s'
                    AND am.state = 'posted'
                    """ % (account_id, company_id, str(from_date))
            self._cr.execute(SQL)
            result = self._cr.dictfetchall()
        if result and result[0].get('debit') and result[0].get('credit'):
            result = [result[0].get('debit'), result[0].get('credit'), result[0].get('debit') - result[0].get('credit')]
        elif result and result[0].get('debit') and not result[0].get('credit'):
            result = [result[0].get('debit'), 0.0, result[0].get('debit') - 0.0]
        elif result and not result[0].get('debit') and result[0].get('credit'):
            result = [0.0, result[0].get('credit'), 0.0 - result[0].get('credit')]
        else:
            result = [0.0, 0.0, 0.0]
        return result

    def _get_accounts(self, accounts, display_account):
        """ compute the balance, debit and credit for the provided accounts
            :Arguments:
                `accounts`: list of accounts record,
                `display_account`: it's used to display either all accounts or those accounts which balance is > 0
            :Returns a list of dictionary of Accounts with following key and value
                `name`: Account name,
                `code`: Account code,
                `credit`: total amount of credit,
                `debit`: total amount of debit,
                `balance`: total amount of balance,
        """

        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"','')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        # compute the balance, debit and credit for the provided accounts
        request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
                   " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.id in account_result:
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        date_from = data.get('form') and data.get('form').get('date_from')
        date_to = data.get('form') and data.get('form').get('date_to')
        state = data['form'] and data['form']['target_move']
        res = self.with_context(date_from=date_from, date_to=date_to, state=state)._get_accounts(accounts, display_account)
        account_result = {}
        for row in res:
            account_result[row.pop('name')] = row
 
        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            if account.name in account_result.keys():
                res['id'] =account.id
                res['debit'] = account_result[account.name].get('debit')
                res['credit'] = account_result[account.name].get('credit')
                res['balance'] = account_result[account.name].get('balance')
            if date_from and data['form'] and data['form']['include_init_balance']:
                init_bal = self._get_init_bal(date_from, account.company_id.id, account.id)
                res['init_bal'] = init_bal[2]
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
                account_res.append(res)
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data,
            'docs': docs,
            'time': time,
            'Accounts': account_res,
        }

