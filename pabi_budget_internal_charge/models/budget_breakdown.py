# -*- coding: utf-8 -*-
from openerp import models, fields, api


class BudgetBreakdownLine(models.Model):
    _inherit = 'budget.breakdown.line'

    @api.model
    def _get_planned_expense_hook(self, breakdown, budget_plan):
        """ We have this hook as with internal charge change it """
        if breakdown.fiscalyear_id.control_ext_charge_only:
            planned_amount = budget_plan and \
                budget_plan.planned_expense_external or 0.0
            return planned_amount
        else:
            return super(BudgetBreakdownLine, self).\
                _get_planned_expense_hook(budget_plan)
