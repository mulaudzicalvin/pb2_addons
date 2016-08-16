# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class DocumentExportConfigLine(models.Model):
    _name = 'document.export.config.lines'
    _description = 'Document Export Configuration Lines'

    @api.constrains('sequence', 'length')
    def _check_sequence(self):
        for line in self:
            if line.sequence <= 0:
                raise UserError(_('Sequence must be greater then zero.'))
            if line.length <= 0:
                raise UserError(_('Length must be greater then zero.'))

    header_configure_id = fields.Many2one(
        'document.export.config',
        string='Header Configuration',
    )
    footer_configure_id = fields.Many2one(
        'document.export.config',
        string='Footer Configuration',
    )
    invoice_configure_id = fields.Many2one(
        'document.export.config',
        string='Invoice Detail Configuration',
    )
    detail_configure_id = fields.Many2one(
        'document.export.config',
        string='Detail Configuration',
    )
    sequence = fields.Integer(
        string='Sequence',
        required=True,
    )
    field_code = fields.Text(
        string='Python Code',
        required=False,
    )
    length = fields.Integer(
        string='Length',
        required=True,
    )
    mandatory = fields.Boolean(
        string='Mandatory?',
    )
    notes = fields.Char(
        string='Remarks',
    )
    default_value = fields.Char(
        string='Default Value',
    )
    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=False,
    )


class DocumentExportConfig(models.Model):
    _name = 'document.export.config'
    _description = 'Document Export Configuration'

    name = fields.Char(
        string="Name",
        required=True,
    )
    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today(),
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        required=False,
        default=lambda self: self.env.uid,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=False,
        default=lambda self: self.env['res.company'].
        _company_default_get('document.export.config'),
    )
    header_config_line_ids = fields.One2many(
        'document.export.config.lines',
        'header_configure_id',
        string='Header Configurations',
    )
    footer_config_line_ids = fields.One2many(
        'document.export.config.lines',
        'footer_configure_id',
        string='Footer Configurations',
    )
    invoice_config_line_ids = fields.One2many(
        'document.export.config.lines',
        'invoice_configure_id',
        string='Invoice Configurations',
    )
    detail_config_line_ids = fields.One2many(
        'document.export.config.lines',
        'detail_configure_id',
        string='Details Configurations',
    )
    delimiter_symbol = fields.Char(
        string="Joining Delimiter",
        required=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Payment Method',
        required=True,
    )
