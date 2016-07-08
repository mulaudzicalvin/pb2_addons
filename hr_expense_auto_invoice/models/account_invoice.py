# -*- coding: utf-8 -*-

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    expense_id = fields.Many2one(
        'hr.expense.expense',
        string="Expense Ref",
    )

    @api.multi
    def confirm_paid(self):
        expenses = self.env['hr.expense.expense'].search([('invoice_id',
                                                           'in', self._ids)])
        if expenses:
            expenses.write({'state': 'paid'})
        return super(AccountInvoice, self).confirm_paid()

    @api.multi
    def action_cancel(self):
        expenses = self.env['hr.expense.expense'].search([('invoice_id',
                                                           'in', self._ids)])
        if expenses:
            expenses.signal_workflow('done_to_accept')
        return super(AccountInvoice, self).action_cancel()

    @api.model
    def _get_invoice_total(self, invoice):
        return invoice.amount_total

#    TODO:
#        - At first, we want to check for amount between Exp and Inv
#        - But for case multi supplier, we can't. So we remove it for now.
#     @api.multi
#     def invoice_validate(self):
#         expenses = self.env['hr.expense.expense'].search([('invoice_id',
#                                                            'in', self._ids)])
#         for expense in expenses:
#             if expense.amount != self._get_invoice_total(expense.invoice_id):
#                 raise except_orm(
#                     _('Amount Error!'),
#                     _("This invoice amount is not equal to amount in "
#                       "expense: %s" % (expense.number,)))
#             expense.signal_workflow('refuse_to_done')
#         return super(AccountInvoice, self).invoice_validate()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    expense_line_ids = fields.Many2many(
        'hr.expense.line',
        'expense_line_invoice_line_rel',
        'invoice_line_id',
        'expense_line_id',
        readonly=True,
        copy=False,
    )
