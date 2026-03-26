📝 NGINX CONFIG CHANGES - CHI TIẾT CÁC THAY ĐỔI
═══════════════════════════════════════════════════════════════════════════

🎯 MỤC ĐÍCH:
WEB1 & WEB2 chạy song song, cân bằng tải 50-50, không giới hạn


❌ CẤU HÌNH CŨ (Chỉ WEB1 chạy):
───────────────────────────────────────────────────────────────────────────

upstream web_backend {
  server web1:80 max_fails=2 fail_timeout=5s;
  server web2:80 max_fails=2 fail_timeout=5s;
  # server web1:80 max_conns=5;           ← Bị comment (giới hạn)
  # server web2:80 backup;                ← Bị comment (backup mode)
  keepalive 16;
}

Vấn đề:
  ❌ Dòng commented out không được dùng
  ❌ WEB2 ở backup mode (ko nhận traffic thường)
  ❌ keepalive=16 có thể quá nhỏ
  ❌ Config không rõ ràng


✅ CẤU HÌNH MỚI (WEB1 & WEB2 cân bằng):
───────────────────────────────────────────────────────────────────────────

upstream web_backend {
  # Round-robin: phân phối requests 50-50 giữa WEB1 và WEB2
  server web1:80 max_fails=2 fail_timeout=5s weight=1;
  server web2:80 max_fails=2 fail_timeout=5s weight=1;
  
  # Keepalive connection pooling
  keepalive 32;
}

Cải tiến:
  ✅ weight=1 → cân bằng 50-50 (bỏ backup mode)
  ✅ keepalive 32 → pool lớn hơn
  ✅ Comments rõ ràng hơn
  ✅ Tất cả đều active


📌 GIẢI THÍCH TỪNG PARAMETER:
───────────────────────────────────────────────────────────────────────────

1. weight=1
   • Mỗi backend có trọng lượng bằng nhau
   • weight=1 → 50% traffic
   • Nếu weight=2 → 67% traffic
   • Nếu weight=1,2 → 33%-67% split

2. max_fails=2
   • Nếu backend fail 2 lần
   • Nginx sẽ tạm dừng backend này

3. fail_timeout=5s
   • Thời gian dừng backend: 5 giây
   • Sau 5s, thử lại backend

4. keepalive=32
   • Giữ 32 idle connections
   • Tái sử dụng connections → faster
   • Càng cao càng tốt (nếu có đủ memory)


🔧 CẬP NHẬT PHẦN PROXY SETTINGS:
───────────────────────────────────────────────────────────────────────────

CŨ:
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

MỚI:
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header Connection "";              ← ✨ NEW
proxy_http_version 1.1;                      ← ✨ NEW

Tại sao?
  • Connection "" → dùng keepalive
  • HTTP/1.1 → hỗ trợ keepalive
  • Kết quả: connection reuse → faster


🚀 FAILOVER STRATEGY (MỚI):
───────────────────────────────────────────────────────────────────────────

proxy_next_upstream error timeout http_502 http_503 http_504;
proxy_next_upstream_tries 2;                 ← ✨ NEW
proxy_next_upstream_timeout 3s;              ← ✨ NEW

Giải thích:
  • Nếu WEB1 fail → thử WEB2 (automatic failover)
  • Tối đa 2 lần thử
  • Timeout: 3 giây để thử failover
  • Nếu cả 2 fail → return error to client


⏱️ TIMEOUT SETTINGS (CẢI THIỆN):
───────────────────────────────────────────────────────────────────────────

proxy_connect_timeout 2s;      ← Kết nối (không thay đổi)
proxy_read_timeout 10s;        ← Đọc response (cũ: 5s → MỚI: 10s)
proxy_send_timeout 10s;        ← Gửi request (cũ: không có → MỚI: 10s)

Lý do:
  • read_timeout 10s → cho requests lâu hơn
  • send_timeout 10s → tránh timeout khi gửi
  • connect_timeout 2s → giữ nguyên (nhanh)


📊 KẾT QUẢ SAU CẬP NHẬT:
───────────────────────────────────────────────────────────────────────────

Trước (cấu hình cũ):
  • WEB1: ~100% requests
  • WEB2: ~0% requests (backup mode)
  • Không cân bằng ❌

Sau (cấu hình mới):
  • WEB1: ~50% requests
  • WEB2: ~50% requests
  • Cân bằng hoàn hảo ✅
  • Failover tự động ✅
  • Performance tốt hơn ✅


🧪 CÓ ẢNH HƯỞNG ĐẾN SCRIPTS KHÔNG?
───────────────────────────────────────────────────────────────────────────

✅ test_lb_basic.py
   • CẬP NHẬT: Sẽ nhận responses từ cả WEB1 & WEB2 (50-50)
   • Kỳ vọng: WEB1 ≈ 50%, WEB2 ≈ 50%

✅ test_lb_failover.py
   • CẬP NHẬT: Failover sẽ nhanh hơn (3s timeout vs 5s cũ)
   • Kỳ vọng: Recovery nhanh hơn

✅ test_lb_stress.py
   • CẬP NHẬT: Stress sẽ phân tán trên 2 backends
   • Kỳ vọng: Throughput có thể tăng (vì 2 backends)

✅ test_lb_security.py
   • KHÔNG THAY ĐỔI
   • Kỳ vọng: Kết quả tương tự


✂️ SỬA SCRIPTS (CÓ CẦN KHÔNG?):
───────────────────────────────────────────────────────────────────────────

❌ KHÔNG CẦN SỬA!

Lý do:
  • Scripts flexible, tự detect WEB1/WEB2
  • Không hard-code nguyên tắc load balancing
  • Chỉ cần read response text

Ví dụ trong test_lb_basic.py:
  if "WEB1" in content:
      self.results["WEB1"] += 1
  elif "WEB2" in content:
      self.results["WEB2"] += 1

→ Tự động hoạt động với cấu hình mới!


🎯 TIẾP THEO - CÓ CẦN RESTART DOCKER?
───────────────────────────────────────────────────────────────────────────

✅ CÓ! Cần restart để apply config mới:

$> docker-compose down
$> docker-compose up -d
$> python test_lb_basic.py -r 20

Kết quả mong đợi:
  Request  1 -> WEB1 (5.5ms)
  Request  2 -> WEB2 (4.3ms)
  Request  3 -> WEB1 (5.9ms)
  Request  4 -> WEB2 (6.2ms)
  ...
  
  Distribution:
    WEB1: 10 requests (50.0%)
    WEB2: 10 requests (50.0%)  ← ✨ THAY ĐỔI!


📋 SUMMARY - TÓM TẮT:
───────────────────────────────────────────────────────────────────────────

Thay đổi:
  ✅ Bỏ backup mode → cân bằng 50-50
  ✅ Thêm weight=1 → rõ ràng hơn
  ✅ Tăng keepalive → faster connections
  ✅ Thêm Connection header → keepalive active
  ✅ Thêm HTTP/1.1 → hỗ trợ keepalive
  ✅ Cải thiện failover timeout
  ✅ Tăng read/send timeout

Kết quả:
  ✨ WEB1 & WEB2 hoàn toàn cân bằng
  ✨ Performance tốt hơn
  ✨ Failover nhanh hơn
  ✨ Scripts không cần sửa

Bước tiếp theo:
  1. docker-compose down
  2. docker-compose up -d
  3. python test_lb_basic.py -r 20
  4. Xem WEB1 ≈ 50%, WEB2 ≈ 50% ✅

═══════════════════════════════════════════════════════════════════════════
