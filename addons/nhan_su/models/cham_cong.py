# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Bảng chấm công nhân viên'
    _rec_name = 'display_name'
    _order = 'ngay_cham desc, nhan_vien_id'

    nhan_vien_id = fields.Many2one(
        'nhan_vien',
        string='Nhân viên',
        required=True,
        ondelete='cascade'
    )
    
    ngay_cham = fields.Date(
        string='Ngày chấm công',
        required=True,
        default=fields.Date.today
    )
    
    gio_vao = fields.Datetime(
        string='Giờ vào',
        required=True
    )
    
    gio_ra = fields.Datetime(
        string='Giờ ra',
        required=False
    )
    
    so_gio_lam = fields.Float(
        string='Số giờ làm việc',
        compute='_compute_so_gio_lam',
        store=True,
        digits=(16, 2)
    )
    
    trang_thai = fields.Selection(
        [
            ('chua_cham', 'Chưa chấm công'),
            ('da_vao', 'Đã vào'),
            ('da_ra', 'Đã ra')
        ],
        string='Trạng thái',
        compute='_compute_trang_thai',
        store=True,
        default='chua_cham'
    )
    
    ghi_chu = fields.Text(string='Ghi chú')
    
    display_name = fields.Char(
        string='Tên hiển thị',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('nhan_vien_id', 'ngay_cham')
    def _compute_display_name(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_cham:
                record.display_name = f"{record.nhan_vien_id.ho_va_ten} - {record.ngay_cham}"
            else:
                record.display_name = 'Chấm công'
    
    @api.depends('gio_vao', 'gio_ra')
    def _compute_so_gio_lam(self):
        for record in self:
            if record.gio_vao and record.gio_ra:
                delta = record.gio_ra - record.gio_vao
                record.so_gio_lam = delta.total_seconds() / 3600.0
            else:
                record.so_gio_lam = 0.0
    
    @api.depends('gio_vao', 'gio_ra')
    def _compute_trang_thai(self):
        for record in self:
            if record.gio_vao and record.gio_ra:
                record.trang_thai = 'da_ra'
            elif record.gio_vao:
                record.trang_thai = 'da_vao'
            else:
                record.trang_thai = 'chua_cham'
    
    @api.constrains('gio_vao', 'gio_ra')
    def _check_gio_lam_viec(self):
        for record in self:
            if record.gio_vao and record.gio_ra:
                if record.gio_ra < record.gio_vao:
                    raise ValidationError("Giờ ra phải lớn hơn giờ vào!")
                # Kiểm tra số giờ làm việc không quá 24 giờ
                delta = record.gio_ra - record.gio_vao
                if delta.total_seconds() / 3600.0 > 24:
                    raise ValidationError("Số giờ làm việc không được vượt quá 24 giờ!")
    
    @api.constrains('nhan_vien_id', 'ngay_cham')
    def _check_cham_cong_trung(self):
        for record in self:
            if record.nhan_vien_id and record.ngay_cham:
                existing = self.env['cham_cong'].search([
                    ('nhan_vien_id', '=', record.nhan_vien_id.id),
                    ('ngay_cham', '=', record.ngay_cham),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(f"Đã tồn tại bản ghi chấm công cho nhân viên {record.nhan_vien_id.ho_va_ten} vào ngày {record.ngay_cham}!")
    
    _sql_constraints = [
        ('unique_nhan_vien_ngay', 'unique(nhan_vien_id, ngay_cham)', 
         'Mỗi nhân viên chỉ được chấm công một lần trong một ngày!')
    ]

