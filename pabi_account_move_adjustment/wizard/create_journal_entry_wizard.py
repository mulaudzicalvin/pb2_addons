# -*- coding: utf-8 -*-
import ast
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class CreateJournalEntryWizard(models.TransientModel):
    _name = 'create.journal.entry.wizard'

    type = fields.Selection(
        [('budget', 'Adjust Budget (JV)'),
         ('no_budget', 'Adjust No-Budget (JN)')],
        string='Type of Adjustment',
        required=True,
    )

    # @api.model
    # def view_init(self, fields_list):
    #     invoice_id = self._context.get('active_id')
    #     invoice = self.env['account.invoice'].browse(invoice_id)
    #     if invoice.adjust_move_id:
    #         raise ValidationError(
    #             _('The adjustmnet journal entry already created!'))

    @api.multi
    def create_journal_entry(self):
        self.ensure_one()
        TYPES = {
            'budget': {'action': 'pabi_account_move_adjustment.'
                                 'action_journal_adjust_budget',
                       'view': 'pabi_account_move_adjustment.'
                               'view_journal_adjust_budget_form'},
            'no_budget': {'action': 'pabi_account_move_adjustment.'
                                    'action_journal_adjust_no_budget',
                          'view': 'pabi_account_move_adjustment.'
                                  'view_journal_adjust_no_budget_form'},
        }
        action = self.env.ref(TYPES[self.type]['action'])
        view = self.env.ref(TYPES[self.type]['view'])
        result = action.read()[0]
        result.update({'view_mode': 'form',
                       'target': 'current',
                       'view_id': view.id,
                       'view_ids': False,
                       'views': False})
        ctx = ast.literal_eval(result['context'])
        invoice_id = self._context.get('active_id')
        invoice = self.env['account.invoice'].browse(invoice_id)
        ctx.update({'default_ref': invoice.number})
        result['context'] = ctx
        return result