from odoo import models, fields

class DanhSachChungChiBangCap(models.Model):
    _name = 'danh_sach_chung_chi_bang_cap'
    _description = 'Bảng danh sách chứng chỉ bằng cấp'

    chung_chi_bang_cap_id = fields.Many2one(
        "chung_chi_bang_cap", 
        string="Chứng chỉ bằng cấp", 
        required=True
    )
    
    nhan_vien_id = fields.Many2one(
        "nhan_vien",
        string="Nhân viên", 
        required=True
    )

    ghi_chu = fields.Char("Ghi chú")

    # Trường Related lấy từ model nhan_vien
    ma_dinh_danh = fields.Char(
        string="Mã định danh", 
        related='nhan_vien_id.ma_dinh_danh',
        readonly=True,
        store=True  
    )
    
    tuoi = fields.Integer(
        string="Tuổi", 
        related='nhan_vien_id.tuoi',
        readonly=True
    )