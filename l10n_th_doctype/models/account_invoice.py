# -*- coding: utf-8 -*-
from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    doctype_id = fields.Many2one(
        'res.doctype',
        string='Doctype',
        compute='_compute_doctype',
        store=True,
        readonly=True,
    )

    @api.one
    @api.depends('type')
    def _compute_doctype(self):
        ttype = self.type
        if self.is_debitnote:
            ttype += '_debitnote'
        doctype = self.env['res.doctype'].search([('refer_type', '=',
                                                   ttype)], limit=1)
        self.doctype_id = doctype.id

    @api.multi
    def action_move_create(self):
        for invoice in self:
            invoice = invoice.with_context(doctype_id=invoice.doctype_id.id)
            super(AccountInvoice, invoice).action_move_create()
        return True

        # for invoice in self:
        #     if invoice.doctype_id.sequence_id:
        #         # Get doctype sequence for document number
        #         sequence_id = invoice.doctype_id.sequence_id.id
        #         fiscalyear_id = invoice.period_id.fiscalyear_id.id
        #         invoice.number = self.\
        #             with_context(fiscalyear_id=fiscalyear_id).\
        #             env['ir.sequence'].next_by_id(sequence_id)
        #         # Use document number for journal entry
        #         invoice.move_id.ref = invoice.number
        # return result
