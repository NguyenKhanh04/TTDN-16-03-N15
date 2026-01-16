import re
from odoo import models, fields, api
from markupsafe import Markup

class AssetAIAssistant(models.Model):
    _name = 'asset.ai.assistant'
    _description = 'AI Assistant Chat'

    def _default_chat_history(self):
        greeting = "Xin chào! Tôi là Trợ lý AI của hệ thống Quản lý Tài sản & Phòng họp. Tôi có thể giúp bạn tìm phòng họp trống, tra cứu vị trí tài sản hoặc xem ai là người phụ trách thiết bị. Hãy yêu cầu tôi nhé!"
        ai_html = f'''
            <div style="margin-bottom: 25px; display: flex; justify-content: flex-start; align-items: flex-start;">
                <div style="max-width: 85%; background: #ffffff; color: #333; padding: 12px 18px; border-radius: 18px 18px 18px 0; border: 1px solid #e0e0e0; box-shadow: 2px 4px 12px rgba(0,0,0,0.08); border-left: 5px solid #28a745;">
                    <b style="font-size: 13px; display: block; margin-bottom: 6px; color: #28a745; text-transform: uppercase; letter-spacing: 0.5px;">🤖 AI Trợ lý:</b>
                    <div style="font-size: 15px; line-height: 1.5;">{greeting}</div>
                </div>
            </div>
        '''
        return Markup(ai_html)

    query = fields.Char(string="Bạn nói gì đó...", help="Hỏi tôi về phòng họp hoặc tài sản!")
    chat_history = fields.Html(string="Lịch sử trò chuyện", readonly=True, sanitize=False, default=_default_chat_history)

    def action_send(self):
        self.ensure_one()
        if not self.query:
            return

        user_msg = self.query.strip().lower()
        response = self._get_ai_response(user_msg)

        # Cấu trúc tin nhắn Chat cải tiến với giao diện dạng ô (Card UX)
        user_html = f'''
            <div style="margin-bottom: 20px; display: flex; justify-content: flex-end; align-items: flex-start;">
                <div style="max-width: 80%; background: #0084ff; color: white; padding: 10px 16px; border-radius: 18px 18px 0 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); position: relative;">
                    <b style="font-size: 13px; display: block; margin-bottom: 4px; color: #e1f5fe;">Bạn:</b>
                    <span style="font-size: 15px;">{self.query}</span>
                </div>
            </div>
        '''
        
        ai_html = f'''
            <div style="margin-bottom: 25px; display: flex; justify-content: flex-start; align-items: flex-start;">
                <div style="max-width: 85%; background: #ffffff; color: #333; padding: 12px 18px; border-radius: 18px 18px 18px 0; border: 1px solid #e0e0e0; box-shadow: 2px 4px 12px rgba(0,0,0,0.08); border-left: 5px solid #28a745;">
                    <b style="font-size: 13px; display: block; margin-bottom: 6px; color: #28a745; text-transform: uppercase; letter-spacing: 0.5px;">🤖 AI Trợ lý:</b>
                    <div style="font-size: 15px; line-height: 1.5;">{response}</div>
                </div>
            </div>
        '''
        
        # Cập nhật lịch sử và cuộn xuống (thêm khoảng trắng ở cuối để dễ nhìn)
        self.chat_history = (self.chat_history or "") + Markup(user_html) + Markup(ai_html)
        self.query = ""

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'asset.ai.assistant',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _get_ai_response(self, text):
        """Hệ thống xử lý ngôn ngữ tự nhiên (NLP) tiếng Việt cải tiến"""
        
        # 1. Intent: Tìm phòng họp (Room Search)
        # Các mẫu: "tìm phòng", "phòng cho 10 người", "cần phòng họp", "kiếm phòng"
        room_keywords = ['phòng', 'phong', 'tìm', 'tim', 'kiếm', 'kiem', 'cần', 'can']
        if any(kw in text for kw in room_keywords):
            # Tìm số lượng người (capacity)
            match_num = re.search(r'(\d+)', text)
            if match_num:
                num = int(match_num.group(1))
                rooms = self.env['meeting.room'].search([
                    ('status', '=', 'free'),
                    ('capacity', '>=', num)
                ], order='capacity asc', limit=1)
                
                if rooms:
                    return f"Vâng, tôi đã tìm thấy phòng <b>{rooms.name}</b> ở <b>{rooms.location or 'vị trí chưa xác định'}</b>. Phòng này có sức chứa {rooms.capacity} người và hiện đang trống. Bạn có muốn tôi giữ chỗ không?"
                else:
                    return f"Hiện tại tôi không tìm thấy phòng nào còn trống đủ cho {num} người. Bạn có muốn tôi kiểm tra các khung giờ khác không?"

        # 2. Intent: Tra cứu tài sản (Asset Inquiry)
        # Các mẫu: "tài sản máy chiếu", "máy tính đâu", "tìm máy in", "thiết bị", "04", "TB001"
        asset_keywords = ['tài sản', 'tai san', 'thiết bị', 'thiet bi', 'máy', 'may', 'bàn', 'ghế', 'laptop']
        
        # Lấy các từ quan trọng từ câu truy vấn (loại bỏ từ dừng cơ bản)
        query_words = [w for w in text.split() if len(w) > 1]
        
        target_asset = False
        
        # Chiến lược 1: Tìm theo mã tài sản chính xác trước
        if query_words:
            for word in query_words:
                found = self.env['asset.management'].search([('code', '=ilike', word)], limit=1)
                if found:
                    target_asset = found
                    break
        
        # Chiến lược 2: Nếu chưa thấy, tìm theo tên tài sản
        if not target_asset and any(kw in text for kw in asset_keywords + ['tìm', 'tim', 'kiếm', 'kiem']):
            # Loại bỏ các từ khóa chung để tìm tên tài sản thực tế
            clean_text = text
            for kw in asset_keywords + ['tìm', 'tim', 'kiếm', 'kiem', 'đâu', 'ở đâu', 'o dau']:
                clean_text = clean_text.replace(kw, '').strip()
            
            if clean_text:
                # Tìm kiếm ưu tiên khớp tên hoàn toàn hoặc chứa trong tên
                target_asset = self.env['asset.management'].search([
                    '|', ('name', '=ilike', clean_text), ('name', 'ilike', clean_text)
                ], limit=1)

        # Chiến lược 3: Duyệt danh sách (fallback cuối cùng cho trường hợp tên nằm trong câu phức tạp)
        if not target_asset and any(kw in text for kw in asset_keywords):
            # Chỉ search những tài sản có tên xuất hiện trong text
            all_assets = self.env['asset.management'].search([], limit=200)
            for asset in all_assets:
                if asset.name.lower() in text:
                    target_asset = asset
                    break
            
        if target_asset:
            dept = target_asset.managing_unit_id.ten_phong_ban if target_asset.managing_unit_id else "chưa có đơn vị cụ thể"
            state_label = dict(self.env['asset.management']._fields['state'].selection).get(target_asset.state, target_asset.state)
            return f"Tài sản <b>{target_asset.name}</b> (Mã: {target_asset.code}) đang có trạng thái: <b>{state_label}</b>, thuộc quản lý của <b>{dept}</b>. Ngày mua: {target_asset.purchase_date or 'không rõ'}."
            
        # Thêm tìm kiếm theo loại tài sản
        if any(kw in text for kw in ['loại', 'loai', 'nhóm', 'nhom']):
            categories = self.env['asset.category'].search([], limit=50)
            for cat in categories:
                if cat.name.lower() in text:
                    return f"Loại tài sản <b>{cat.name}</b> hiện có tổng số {cat.total_count} cái. Trong đó {cat.stored_count} cái đang lưu trữ và {cat.borrowed_count} cái đang cho mượn."

        if any(kw in text for kw in asset_keywords):
            return "Bạn đang muốn tìm tài sản nào? Hãy cho tôi biết tên hoặc mã số của nó nhé (ví dụ: 'Tìm máy chiếu' hoặc 'Máy in ở đâu')."

        # 3. Intent: Hỏi về người phụ trách hoặc phòng ban (HR integration)
        if any(word in text for word in ['ai', 'người', 'phụ trách', 'quản lý', 'đơn vị']):
            if 'phòng' in text or 'phong' in text:
                # Tìm phòng được nhắc đến
                rooms = self.env['meeting.room'].search([], limit=50)
                for r in rooms:
                    if r.name.lower() in text:
                        resp = r.responsible_id.ho_va_ten if r.responsible_id else "hiện chưa có ai"
                        return f"Người chịu trách nhiệm chính cho phòng <b>{r.name}</b> là <b>{resp}</b>."

        # 4. Intent: Thống kê tài sản trong phòng (Asset Statistics in Room)
        # Các mẫu: "thống kê tài sản phòng họp A", "liệt kê thiết bị phòng VIP", "tài sản phòng 01 có gì"
        if any(kw in text for kw in ['thống kê', 'liệt kê', 'danh sách', 'có những gì', 'có gì']):
            if 'phòng' in text or 'phong' in text:
                 # Tìm phòng được nhắc đến
                rooms = self.env['meeting.room'].search([], limit=50)
                target_room = False
                for r in rooms:
                     # Simple fuzzy match: if room name is in query
                    if r.name.lower() in text.lower():
                        target_room = r
                        break
                
                if target_room:
                    assets = target_room.asset_ids
                    if not assets:
                         return f"Phòng <b>{target_room.name}</b> hiện tại chưa có tài sản nào được ghi nhận."
                    
                    # Build list HTML
                    asset_list_html = "<ul>"
                    for asset in assets:
                        asset_list_html += f"<li><b>[{asset.code}]</b> - {asset.name}</li>"
                    asset_list_html += "</ul>"
                    
                    return f"Phòng <b>{target_room.name}</b> hiện có <b>{len(assets)}</b> tài sản:<br/>{asset_list_html}"
                else:
                    return "Bạn muốn xem thống kê tài sản của phòng nào? Vui lòng nói rõ tên phòng (ví dụ: 'thống kê tài sản phòng họp lớn')."

        # 4. Intent: Chào hỏi (Greeting)
        if any(word in text for word in ['chào', 'hello', 'hi', 'bắt đầu']):
            greeting = "Xin chào! Tôi là Trợ lý AI của hệ thống Quản lý Tài sản & Phòng họp. Tôi có thể giúp bạn tìm phòng họp trống, tra cứu vị trí tài sản hoặc xem ai là người phụ trách thiết bị. Hãy yêu cầu tôi nhé!"
            return greeting

        return "Xin lỗi, tôi chưa hiểu ý bạn lắm. Bạn có thể thử nói: 'Tìm phòng cho 10 người' hoặc 'Máy chiếu đang ở đâu?'"
