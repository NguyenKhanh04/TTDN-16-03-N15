# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AssetBorrowSlip(models.Model):
    _name = 'asset.borrow.slip'
    _description = 'Phiếu mượn tài sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Mã phiếu", required=True, copy=False, readonly=True, default='New')
    user_id = fields.Many2one('nhan_vien', string="Người mượn", required=True)
    date_borrow = fields.Date(string="Ngày mượn", default=fields.Date.today, required=True)
    date_return = fields.Date(string="Ngày trả dự kiến")
    
    asset_ids = fields.Many2many('asset.management', string="Danh sách tài sản", domain=[('state', '=', 'stored')])
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('borrowed', 'Đang mượn'),
        ('returned', 'Đã trả')
    ], string="Trạng thái", default='draft', track_visibility='onchange')
    
    note = fields.Text(string="Ghi chú")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('asset.borrow.slip') or 'New'
        return super(AssetBorrowSlip, self).create(vals)

    def action_confirm_borrow(self):
        for record in self:
            if not record.asset_ids:
                raise ValidationError("Vui lòng chọn tài sản để mượn!")
            
            # Check availability again just in case
            for asset in record.asset_ids:
                if asset.state != 'stored':
                    raise ValidationError(f"Tài sản {asset.name} hiện không khả dụng (Trạng thái: {asset.state})!")
            
            # Update assets state and log allocation
            for asset in record.asset_ids:
                asset.write({
                    'state': 'borrowed',
                    'assigned_to_id': record.user_id.id
                })
                
                self.env['asset.allocation'].create({
                    'asset_id': asset.id,
                    'user_id': record.user_id.id,
                    'date_start': record.date_borrow,
                    'state': 'active'
                })
            
            record.state = 'borrowed'

    def action_return_assets(self):
        for record in self:
            # Update assets state back to stored
            for asset in record.asset_ids:
                asset.write({
                    'state': 'stored',
                    'assigned_to_id': False
                })
                
                # Close allocation log
                allocation = self.env['asset.allocation'].search([
                    ('asset_id', '=', asset.id),
                    ('state', '=', 'active'),
                    ('user_id', '=', record.user_id.id)
                ], limit=1)
                
                if allocation:
                    allocation.write({
                        'state': 'returned',
                        'date_end': fields.Date.today()
                    })
            
            record.state = 'returned'
