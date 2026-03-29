# Đồ án: Triển khai Nginx Load Balancer (Thuật toán Round-Robin)

**Nhóm thực hiện:** 16 [BonChangLinhNguLam] 

---

## 📌 Giới thiệu dự án
Dự án này triển khai một hệ thống Load Balancer sử dụng Nginx đứng trước 2 Web Server độc lập. 

Khác với cấu hình dự phòng thông thường, hệ thống này được thiết lập chạy song song hai máy chủ để tối ưu hóa hiệu suất, với các tính năng chính:
* **Thuật toán Round-Robin:** Phân phối đều lượng truy cập theo tỷ lệ 50-50 cho cả WEB1 và WEB2. Cả hai server đều hoạt động hết công suất để phục vụ khách hàng.
* **Cơ chế Failover thông minh:** Tích hợp `proxy_next_upstream`. Nếu Nginx phát hiện WEB1 hoặc WEB2 bị lỗi hoặc sập nguồn, nó sẽ tự động chuyển hướng toàn bộ traffic sang server còn sống ngay lập tức. Đảm bảo dịch vụ web không bao giờ bị gián đoạn.
* **Tối ưu hóa kết nối:** Sử dụng `keepalive` connection pooling để giảm độ trễ khi tạo kết nối mới giữa Nginx và các backend server.

---

## 🛠 Yêu cầu hệ thống
Để chạy bản Demo và bộ Test Suite, máy tính của bạn cần có:
1. **Docker Desktop:** Để chạy hệ thống Nginx và các Web Server dưới dạng container.
2. **Python 3.7+:** Để khởi chạy các kịch bản kiểm thử tự động.
3. **Trình soạn thảo code:** VS Code hoặc bất kỳ IDE nào có Terminal tích hợp.

---

## 🚀 Quick Start & Demo Tự Động

Mở Terminal tại thư mục gốc của dự án và chạy lần lượt các lệnh dưới đây để khởi động và kiểm thử hệ thống:

```bash
# 1. Cài đặt thư viện Python (Chỉ chạy 1 lần đầu tiên)
pip install requests

# 2. Dựng và khởi động hệ thống ngầm qua Docker
docker-compose up -d --build

# 3. Chạy các kịch bản test tự động
python test_lb_basic.py -r 20               # Kịch bản 1: Test tỷ lệ chia đều traffic 50-50
python test_lb_failover.py -r 15            # Kịch bản 2: Test tự động bẻ lái khi tắt nóng 1 server
python test_lb_stress.py -d 30 -t 3 -r 5    # Kịch bản 3: Ép xung hệ thống, đo thời gian phản hồi
python test_lb_security.py                  # Kịch bản 4: Rà quét và phát hiện lỗi bảo mật

# 4. Xem báo cáo kết quả chi tiết (Được tự động sinh ra sau khi chạy test)
cat stress_test_report_*.json
cat failover_report_*.json
cat security_findings_*.json

# 5. Dọn dẹp tài nguyên sau khi hoàn thành Demo
docker-compose down
```
