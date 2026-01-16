# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetCategory(models.Model):
    _name = 'asset.category'
    _description = 'Phân loại tài sản'
    _rec_name = 'name'

    name = fields.Char(string="Tên loại tài sản", required=True)
    code = fields.Char(string="Mã loại")
    description = fields.Text(string="Mô tả")
    
    asset_ids = fields.One2many('asset.management', 'category_id', string="Danh sách tài sản")
    
    # Statistical fields
    total_count = fields.Integer(string="Tổng số lượng", compute="_compute_asset_stats")
    stored_count = fields.Integer(string="Lưu trữ", compute="_compute_asset_stats")
    borrowed_count = fields.Integer(string="Mượn", compute="_compute_asset_stats")
    maintenance_count = fields.Integer(string="Bảo trì", compute="_compute_asset_stats")
    broken_count = fields.Integer(string="Hỏng", compute="_compute_asset_stats")

    @api.depends('asset_ids.state')
    def _compute_asset_stats(self):
        for record in self:
            record.total_count = len(record.asset_ids)
            record.stored_count = len(record.asset_ids.filtered(lambda a: a.state == 'stored'))
            record.borrowed_count = len(record.asset_ids.filtered(lambda a: a.state == 'borrowed'))
            record.maintenance_count = len(record.asset_ids.filtered(lambda a: a.state == 'maintenance'))
            record.broken_count = len(record.asset_ids.filtered(lambda a: a.state == 'broken'))

class AssetManagement(models.Model):
    _name = 'asset.management'
    _description = 'Quản lý tài sản'
    _rec_name = 'name'

    code = fields.Char(string="Mã Tài sản...", required=True)
    name = fields.Char(string="Tên Tài sản", required=True)
    category_id = fields.Many2one('asset.category', string="Loại tài sản")
    asset_type = fields.Selection([
        ('electronic', 'Điện tử'),
        ('furniture', 'Nội thất'),
        ('vehicle', 'Xe cộ'),
        ('other', 'Khác')
    ], string="Loại thiết bị", default='other')
    
    serial_number = fields.Char(string="Số serial...")
    purchase_date = fields.Date(string="Ngày mua")
    warranty_date = fields.Date(string="Ngày hết hạn...")
    purchase_value = fields.Float(string="Giá tiền mua...")
    purchase_value = fields.Float(string="Giá tiền mua...")
    current_value = fields.Float(string="Giá trị hiện tại...", compute="_compute_current_value", store=True)
    
    state = fields.Selection([
        ('stored', 'Lưu trữ'),
        ('borrowed', 'Mượn'),
        ('maintenance', 'Bảo trì'),
        ('broken', 'Hỏng'),
        ('liquidated', 'Thanh lý')
    ], string="Trạng thái...", default='stored')

    managing_unit_id = fields.Many2one('phong_ban', string="Đơn vị quản lý")
    assigned_to_id = fields.Many2one('nhan_vien', string="Người sử dụng")
    room_id = fields.Many2one('meeting.room', string="Phòng họp")
    profile = fields.Text(string="Mô tả")
    
    maintenance_ids = fields.One2many('asset.maintenance', 'asset_id', string="Lịch sử bảo trì")
    allocation_ids = fields.One2many('asset.allocation', 'asset_id', string="Lịch sử cấp phát")

    # Depreciation & Inventory
    useful_life_years = fields.Integer(string="Thời gian sử dụng (năm)", default=5)
    last_inventory_date = fields.Date(string="Ngày kiểm kê gần nhất")
    liquidation_date = fields.Date(string="Ngày thanh lý")
    liquidation_price = fields.Float(string="Giá thanh lý")
    
    @api.depends('purchase_value', 'purchase_date', 'useful_life_years')
    def _compute_current_value(self):
        for record in self:
            if record.purchase_value and record.purchase_date and record.useful_life_years:
                # Calculate years passed
                days_passed = (fields.Date.today() - record.purchase_date).days
                years_passed = days_passed / 365.0
                
                # Linear depreciation
                depreciation_amount = (record.purchase_value / record.useful_life_years) * years_passed
                
                new_value = record.purchase_value - depreciation_amount
                record.current_value = max(new_value, 0)
            else:
                record.current_value = record.purchase_value

    def action_confirm_allocation(self):
        for record in self:
            if not record.assigned_to_id:
                pass # Should raise error or handled by view required
            
            record.write({'state': 'borrowed'})
            self.env['asset.allocation'].create({
                'asset_id': record.id,
                'user_id': record.assigned_to_id.id,
                'date_start': fields.Date.today(),
                'state': 'active'
            })

    def action_return(self):
        for record in self:
            # Close active allocation
            allocation = self.env['asset.allocation'].search([
                ('asset_id', '=', record.id),
                ('state', '=', 'active')
            ], limit=1)
            if allocation:
                allocation.write({
                    'state': 'returned',
                    'date_end': fields.Date.today()
                })
            
            record.write({'state': 'stored', 'assigned_to_id': False})

    def action_liquidate(self):
        for record in self:
            record.write({
                'state': 'liquidated', 
                'liquidation_date': fields.Date.today(),
                'current_value': 0
            })

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Asset Code must be unique!')
    ]

class AssetMaintenance(models.Model):
    _name = 'asset.maintenance'
    _description = 'Asset Maintenance'

    asset_id = fields.Many2one('asset.management', string="Asset", required=True)
    date = fields.Date(string="Date", default=fields.Date.today)
    description = fields.Text(string="Description", required=True)
    repair_process = fields.Text(string="Repair Process")
    cost = fields.Float(string="Cost")

class AssetAllocation(models.Model):
    _name = 'asset.allocation'
    _description = 'Lịch sử cấp phát tài sản'

    asset_id = fields.Many2one('asset.management', string="Tài sản", required=True)
    user_id = fields.Many2one('nhan_vien', string="Người sử dụng", required=True)
    date_start = fields.Date(string="Ngày bắt đầu", default=fields.Date.today, required=True)
    date_end = fields.Date(string="Ngày kết thúc")
    state = fields.Selection([('active', 'Đang sử dụng'), ('returned', 'Đã trả')], string="Trạng thái", default='active')

# Re-opening AssetManagement to add new methods (Adding them to the existing class would be cleaner if I could insert into the class, but replace_block is better for appending or replacing chunks. 
# Since I need to add fields and methods to AssetManagement which is defined earlier, I might need to use multi_replace or carefully target the class body.)
# Wait, I cannot easily "re-open" a class in Python in the same file by just appending. I must edit the class definition earlier in the file.
# Strategy: I will edit AssetManagement class to add fields and methods. Then I will append AssetAllocation at the end.

# Let's cancel this tool call and do it right. I need to modify AssetManagement first.

