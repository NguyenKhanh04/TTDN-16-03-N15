# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MeetingRoom(models.Model):
    _name = 'meeting.room'
    _description = 'Phòng họp'
    _rec_name = 'name'

    code = fields.Char(string="Mã phòng", required=True)
    name = fields.Char(string="Tên phòng", required=True)
    location = fields.Char(string="Vị trí")
    address = fields.Text(string="Địa chỉ")
    capacity = fields.Integer(string="Sức chứa", default=1)
    status = fields.Selection([
        ('free', 'Trống'),
        ('occupied', 'Đang sử dụng'),
        ('maintenance', 'Bảo trì')
    ], string="Trạng thái", default='free', required=True)

    responsible_id = fields.Many2one('nhan_vien', string="Người phụ trách")
    asset_ids = fields.One2many('asset.management', 'room_id', string="Tài sản trong phòng")
    
    asset_count = fields.Integer(string="Tổng số tài sản", compute="_compute_asset_stats")
    asset_summary = fields.Text(string="Thống kê tài sản", compute="_compute_asset_stats")
    
    maintenance_ids = fields.One2many('room.maintenance', 'room_id', string="Lịch sử bảo trì")

    @api.depends('asset_ids', 'asset_ids.category_id')
    def _compute_asset_stats(self):
        for record in self:
            record.asset_count = len(record.asset_ids)
            
            # Group by category
            stats = {}
            for asset in record.asset_ids:
                cat_name = asset.category_id.name or 'Chưa phân loại'
                if cat_name in stats:
                    stats[cat_name] += 1
                else:
                    stats[cat_name] = 1
            
            summary_list = [f"{cat}: {count}" for cat, count in stats.items()]
            record.asset_summary = "\n".join(summary_list)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Room Code must be unique!')
    ]

class RoomMaintenance(models.Model):
    _name = 'room.maintenance'
    _description = 'Bảo trì phòng họp'

    room_id = fields.Many2one('meeting.room', string="Phòng họp", required=True)
    date = fields.Date(string="Ngày", default=fields.Date.today)
    description = fields.Text(string="Nội dung bảo trì", required=True)
    cost = fields.Float(string="Chi phí")
    status = fields.Selection([('draft', 'Mới'), ('done', 'Hoàn thành')], string="Trạng thái", default='draft')
