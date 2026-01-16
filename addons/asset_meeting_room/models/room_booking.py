# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RoomBooking(models.Model):
    _name = 'room.booking'
    _description = 'Đặt phòng họp'

    room_id = fields.Many2one('meeting.room', string="Phòng họp")
    booker_id = fields.Many2one('nhan_vien', string="Người đặt", required=True)
    
    start_time = fields.Datetime(string="Thời gian bắt đầu", required=True)
    end_time = fields.Datetime(string="Thời gian kết thúc", required=True)
    
    num_participants = fields.Integer(string="Số người tham gia", default=1)
    purpose = fields.Text(string="Mục đích")
    
    ai_recommendation = fields.Text(string="Gợi ý từ AI", readonly=True)

    @api.constrains('start_time', 'end_time', 'room_id')
    def _check_overlap(self):
        for record in self:
            if not record.room_id:
                continue
            overlap = self.env['room.booking'].search([
                ('id', '!=', record.id),
                ('room_id', '=', record.room_id.id),
                ('start_time', '<', record.end_time),
                ('end_time', '>', record.start_time)
            ])
            if overlap:
                raise ValidationError("This room is already booked for the selected time!")

    def action_ai_suggest_room(self):
        """
        AI-based Room Suggestion Logic:
        Finds the best available room based on:
        1. Availability (not booked during the requested time)
        2. Status (must be 'free')
        3. Capacity (best fit: smallest room that fits all participants)
        """
        self.ensure_one()
        if self.num_participants <= 0:
            raise ValidationError("Please enter number of participants.")

        # Find all free rooms
        available_rooms = self.env['meeting.room'].search([
            ('status', '=', 'free'),
            ('capacity', '>=', self.num_participants)
        ])

        # Filter out rooms that are already booked for this time
        suggestions = []
        for room in available_rooms:
            overlap = self.env['room.booking'].search([
                ('room_id', '=', room.id),
                ('start_time', '<', self.end_time),
                ('end_time', '>', self.start_time)
            ])
            if not overlap:
                suggestions.append(room)

        if not suggestions:
            self.ai_recommendation = "Ghi chú AI: Không tìm thấy phòng trống phù hợp với thời gian và số lượng người này."
            return

        # AI Heuristic: Best Fit (minimize wasted capacity)
        # Sort by capacity ascending
        best_room = sorted(suggestions, key=lambda x: x.capacity)[0]
        
        self.room_id = best_room
        self.ai_recommendation = f"Cố vấn AI: Đã gợi ý phòng '{best_room.name}' (Sức chứa: {best_room.capacity}) là lựa chọn tối ưu nhất cho {self.num_participants} người tham gia."

    @api.onchange('room_id')
    def _onchange_room_id(self):
        if self.room_id and self.num_participants > self.room_id.capacity:
            return {
                'warning': {
                    'title': "Capacity Warning",
                    'message': f"Selected room has capacity of {self.room_id.capacity}, but you have {self.num_participants} participants."
                }
            }
