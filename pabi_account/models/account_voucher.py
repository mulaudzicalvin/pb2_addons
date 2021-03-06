# -*- coding: utf-8 -*-
from openerp import models, api, fields, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError
from openerp.addons.l10n_th_account.models.res_partner \
    import INCOME_TAX_FORM


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    invoices_text = fields.Char(
        size=1000,
        compute='_compute_invoices_ref',
        string='Invoices',
        store=True,
    )
    validate_user_id = fields.Many2one(
        'res.users',
        string='Validated By',
        readonly=True,
        copy=False,
    )
    validate_date = fields.Date(
        'Validate On',
        readonly=True,
        copy=False,
    )
    total_ar_amount = fields.Float(
        compute="_compute_total_ar_ap_amount",
        string='Total AR',
        digits_compute=dp.get_precision('Account'),
    )
    total_ap_amount = fields.Float(
        compute="_compute_total_ar_ap_amount",
        string='Total AR',
        digits_compute=dp.get_precision('Account'),
    )
    receipt_type = fields.Selection(
        [('cash', 'Cash'),
         ('credit', 'Credit'),
         ('transfer', 'Transfer'),
         ('cheque', 'Cheque'),
         ],
        string='Receipt Type',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Type to be used in forms. Only avaiable on Customer Receipt",
    )
    narration = fields.Text(
        readonly=False,
    )
    operating_unit_id = fields.Many2one(
        readonly=True, states={'draft': [('readonly', False)]},
    )
    writeoff_operating_unit_id = fields.Many2one(
        readonly=True, states={'draft': [('readonly', False)]},
    )
    currency_rate = fields.Float(
        string='Currency Rate',
        compute='_compute_currency_rate',
        store=True,
    )
    voucher_description = fields.Text(
        string='Voucher Description',
        compute='_compute_voucher_description',
        help="Compute summary description of entire voucher lines",
    )
    income_tax_form = fields.Selection(
        INCOME_TAX_FORM,
        string='Income Tax Form',
        compute='_compute_income_tax_form',
        store=True,
        help="Auto compute from the selected invoice",
    )
    number_preprint = fields.Char(
        string='Preprint Number',
    )
    research_type = fields.Selection(
        [('basic', 'Basic Research'),
         ('applied', 'Applied Research'),
         ],
        string='Research Type',
    )
    contract_number = fields.Char(
        string='Contract Number',
    )
    partner_code = fields.Char(
        string='Partner Code',
        related='partner_id.search_key',
        store=True,
    )
    date = fields.Date(
        string='Posting Date',  # Change label
    )
    date_document = fields.Date(
        string='Document Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        default=lambda self: fields.Date.context_today(self),
    )
    followup_receipt = fields.Selection(
        [('following', 'Following'),
         ('received', 'Received')],
        string='Receipt Followup',
    )
    _sql_constraints = [('number_preprint_uniq', 'unique(number_preprint)',
                        'Preprint Number must be unique!')]

    @api.multi
    def write(self, vals):
        # Set date
        if vals.get('date') and not vals.get('date_document'):
            for rec in self:
                if not rec.date_document:
                    vals['date_document'] = vals['date']
                    break
        return super(AccountVoucher, self).write(vals)

    @api.multi
    @api.constrains('line_ids', 'line_cr_ids', 'line_dr_ids')
    def _check_receipt_no_mixing_taxbranch(self):
        for voucher in self:
            if voucher.type == 'receipt':
                taxbranches = voucher.line_ids.mapped('invoice_taxbranch_id')
                if len(taxbranches) > 1:
                    raise ValidationError(_('Mixing invoices for different '
                                            'tax branch is not allowed!'))

    @api.multi
    @api.depends('line_ids')
    def _compute_income_tax_form(self):
        for voucher in self:
            invoices = voucher.line_ids.mapped('move_line_id.invoice')
            forms = list(set(invoices.filtered('has_wht').
                             mapped('income_tax_form')))
            if forms:
                if len(forms) != 1:
                    raise ValidationError(
                        _('Selected invoices has different Income Tax Form!'))
                voucher.income_tax_form = forms[0]

    @api.multi
    def _compute_voucher_description(self):
        for voucher in self:
            items = []
            description = ''
            for line in voucher.line_ids:
                invoice = line.move_line_id.invoice
                amount = line.amount
                if invoice.internal_number and amount > 0.0:
                    invoice_number = '%10s' % invoice.internal_number
                    amount_str = '%15s' % '{:,.2f}'.format(amount)
                    items.append('%s %s' % (invoice_number, amount_str))
                    if len(items) == 3:
                        description += '      '.join(items) + '\n'
                        items = []
            voucher.voucher_description = description

    @api.multi
    @api.depends('currency_id')
    def _compute_currency_rate(self):
        for rec in self:
            company = rec.company_id
            context = self._context.copy()
            ctx_date = rec.date
            if not ctx_date:
                ctx_date = fields.Date.today()
            context.update({'date': ctx_date})
            # get rate of company currency to current invoice currency
            rate = self.env['res.currency'].\
                with_context(context)._get_conversion_rate(company.currency_id,
                                                           rec.currency_id)
            rec.currency_rate = rate

    @api.multi
    @api.constrains('date_value')
    def _check_date_value_same_period(self):
        for voucher in self:
            if voucher.date_value:
                Period = self.env['account.period']
                period = Period.find(voucher.date_value)[:1]
                if voucher.period_id != period:
                    raise ValidationError(
                        _('Value Date can not be in different '
                          'period as its document!'))

    @api.model
    def _get_related_invoices(self):
        doc_types = ('in_invoice', 'in_refund',)
        if self.type == 'receipt':
            doc_types = ('out_invoice', 'out_refund',)
        AccountInvoice = self.env['account.invoice']
        partner = self.partner_id.id
        invoice_ids =\
            AccountInvoice.search([('state', '=', 'open'),
                                   ('type', 'in', doc_types),
                                   ('partner_id', 'child_of', partner)]).ids
        return invoice_ids

    @api.multi
    def _compute_total_ar_ap_amount(self):
        for record in self:
            invoice_ids = record._get_related_invoices()
            amount = 0.0
            if invoice_ids:
                invoices = self.env['account.invoice'].browse(invoice_ids)
                amount = sum([i.amount_total for i in invoices])
            if record.type == 'receipt':
                record.total_ar_amount = amount
            elif record.type == 'payment':
                record.total_ap_amount = amount

    @api.depends('line_ids')
    def _compute_invoices_ref(self):
        for voucher in self:
            invoices_text = []
            limit = 3
            i = 0
            for line in voucher.line_ids:
                if line.move_line_id and i < limit:
                    if line.move_line_id.document:
                        invoices_text.append(line.move_line_id.document)
                    i += 1
            voucher.invoices_text = ", ".join(invoices_text)
            if len(voucher.line_ids) > limit:
                voucher.invoices_text += ', ...'

    @api.multi
    def action_open_invoices(self):
        self.ensure_one()
        invoice_ids = self._get_related_invoices()
        action_id = False
        if self.type == 'receipt':
            action_id = self.env.ref('account.action_invoice_tree1')
        else:
            action_id = self.env.ref('account.action_invoice_tree2')
        if action_id:
            action = action_id.read([])[0]
            action['domain'] =\
                "[('id','in', [" + ','.join(map(str, invoice_ids)) + "])]"
            return action
        return True

    @api.multi
    def proforma_voucher(self):
        result = super(AccountVoucher, self).proforma_voucher()
        # For NSTDA, not writeoff_amount allowed for Supplier Paymnet
        for rec in self:
            if rec.type == 'payment' and rec.writeoff_amount:
                raise ValidationError(_('Difference Amount must be 0.0 '
                                        'to validate this document!'))
        self.write({'validate_user_id': self.env.user.id,
                    'validate_date': fields.Date.today()})
        return result

    @api.multi
    def recompute_voucher_lines(self, partner_id, journal_id,
                                price, currency_id, ttype, date):
        """ Always check reconcile """
        res = super(AccountVoucher, self).recompute_voucher_lines(
            partner_id, journal_id,
            price, currency_id, ttype, date)
        value = res['value']
        VoucherLine = self.env['account.voucher.line']
        for vtype in ['line_cr_ids', 'line_dr_ids']:
            line_ids = []
            for l in value[vtype]:
                if not isinstance(l, dict):
                    continue
                reconcile = True
                vals = VoucherLine.onchange_reconcile(
                    partner_id, l['move_line_id'], l['amount_original'],
                    reconcile, False, l['amount_unreconciled'])
                vals['value']['reconcile'] = reconcile
                l.update(vals['value'])
                line_ids.append(l)
            value[vtype] = line_ids
        res['value'] = value
        return res


class AccountVoucherLine(models.Model):
    _inherit = 'account.voucher.line'

    invoice_description = fields.Text(
        related='invoice_id.invoice_description',
        string='Invoice Description',
        readonly=True,
    )
    invoice_taxbranch_id = fields.Many2one(
        'res.taxbranch',
        string='Taxbranch',
        compute='_compute_invoice_taxbranch_id',
        # related='move_line_id.invoice.taxbranch_id',
        # store=True,
    )

    @api.multi
    def _compute_invoice_taxbranch_id(self):
        for rec in self:
            rec.invoice_taxbranch_id = rec.move_line_id.invoice.taxbranch_id


class AccountVoucherTax(models.Model):
    _inherit = "account.voucher.tax"

    taxbranch_id = fields.Many2one(
        'res.taxbranch',
        related='invoice_id.taxbranch_id',
        string='Tax Branch',
        readonly=True,
        store=True,
    )

    @api.model
    def _prepare_voucher_tax_detail(self):
        res = super(AccountVoucherTax, self)._prepare_voucher_tax_detail()
        res.update({'taxbranch_id': self.invoice_id.taxbranch_id.id})
        return res

    @api.model
    def move_line_get(self, voucher):
        """ Normal Tax: Use invoice's tax branch for tax move line
            WHT: Use a centralized tax branch """
        res = super(AccountVoucherTax, self).move_line_get(voucher)
        taxbranch_id = False
        for line in voucher.line_ids:
            if line.amount or line.amount_wht or line.amount_retention:
                taxbranch_id = line.invoice_taxbranch_id.id
        tax_move_by_taxbranch = self.env.user.company_id.tax_move_by_taxbranch
        if tax_move_by_taxbranch:
            wht_taxbranch_id = self.env.user.company_id.wht_taxbranch_id.id
            if not wht_taxbranch_id:
                raise ValidationError(
                    _('No Taxbranch for Withholding Tax has been configured!'))
            for r in res:
                if 'tax_code_type' in r and r['tax_code_type'] == 'wht' \
                        and wht_taxbranch_id:
                    r.update({'taxbranch_id': wht_taxbranch_id})
                else:
                    r.update({'taxbranch_id': taxbranch_id})
        return res

    @api.model
    def _prepare_one_move_line(self, t):
        res = super(AccountVoucherTax, self)._prepare_one_move_line(t)
        res['taxinvoice_taxbranch_id'] = t['taxbranch_id']
        return res
