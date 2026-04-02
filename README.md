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
## 🧪 Kịch bản kiểm thử tự động

Hệ thống đi kèm với một kịch bản kiểm thử tự động được bằng Python, bao gồm 3 kịch bản chính nhằm đánh giá toàn diện năng lực của Nginx:

### Kịch bản 1: Đánh giá khả năng phân phối tải cơ bản
* **Mục tiêu:** Xác minh tính chính xác của thuật toán Round-Robin trong điều kiện vận hành bình thường.
* **Cách hoạt động:** Script `test_lb_basic.py` sẽ phát sinh một loạt các request tuần tự gửi đến Node LB. Sau đó, công cụ sẽ phân tích mã nguồn phản hồi để thống kê chính xác số lượng request mà WEB1 và WEB2 đã xử lý, từ đó chứng minh tỷ lệ chia tải đạt mức cân bằng 50-50.

### Kịch bản 2: Đánh giá tính sẵn sàng và khả năng chịu lỗi
* **Mục tiêu:** Kiểm chứng hiệu quả hoạt động của cơ chế tự động chuyển hướng luồng request khi một Node Web gặp sự cố ngừng hoạt động đột ngột.
* **Cách hoạt động:** Script `test_lb_failover.py` sẽ can thiệp trực tiếp vào Docker để tắt nóng WEB2 trong lúc hệ thống đang nhận tải. Công cụ sẽ tự động ghi nhận khả năng Nginx bẻ lái toàn bộ lượng request sang WEB1 (không làm rớt request nào) và tự động chia lại tải đều 50-50 khi WEB2 được bật lên trở lại.

### Kịch bản 3: Đánh giá hiệu năng dưới tải trọng lớn
* **Mục tiêu:** Đo lường thông lượng xử lý và độ trễ phản hồi khi hệ thống đối mặt với lượng truy cập đa luồng cường độ cao.
* **Cách hoạt động:** Script `test_lb_stress.py` ứng dụng kỹ thuật đa luồng để mô phỏng hàng ngàn request dội thẳng vào hệ thống cùng lúc. Kết quả đầu ra sẽ cung cấp các chỉ số hiệu năng chuyên sâu như thời gian phản hồi trung bình, độ trễ tối đa và tỷ lệ xử lý thành công.

--- 

## 🌟 Tính mới & Điểm nhấn kỹ thuật: Cơ chế Tự vệ chủ động (Active Defense & Anti-DDoS)
**Cơ chế hoạt động Rate Limiting:**
Hệ thống sử dụng thuật toán *Leaky Bucket* (thông qua module `ngx_http_limit_req_module`) để giám sát tần suất truy cập của từng địa chỉ IP độc lập. Khi phát hiện một IP có hành vi spam requests vượt ngưỡng cho phép, Node LB sẽ lập tức chặt đứt kết nối, chủ động trả về mã lỗi `503 Service Unavailable` để bảo vệ tài nguyên CPU/RAM cho các Node Web bên trong.

**🧪 Minh chứng thực chiến (Chaos Engineering):**
Khả năng tự vệ này được minh chứng rõ ràng qua Kịch bản Stress Test (`test_lb_stress.py`). Khi cố tình ép xung hệ thống với cường độ cao:
* Các request hợp lệ ban đầu vẫn được phân phối đều (50-50) vào WEB1 và WEB2.
* Các request vượt ngưỡng lập tức bị Nginx chặn đứng. 
* Đặc biệt, trong file báo cáo JSON trả về, số lượng **`Failed` vẫn duy trì ở mức 0**, trong khi các request bị chặn sẽ được đẩy vào nhóm **`Unknown`**. Điều này khẳng định: Hệ thống KHÔNG HỀ BỊ SẬP do quá tải, mà là đang CHỦ ĐỘNG cắt luồng truy cập độc hại, đảm bảo tính sẵn sàng (High Availability) tuyệt đối cho những người dùng hợp lệ khác.

---

## 🚀 Quick Start & Demo Tự Động

Mở Terminal tại thư mục gốc của dự án và chạy lần lượt các lệnh dưới đây để khởi động và kiểm thử hệ thống:

```bash
# 1. Cài đặt thư viện Python (Chỉ chạy 1 lần đầu tiên)
pip install requests

# 2. Dựng và khởi động hệ thống ngầm qua Docker
docker-compose up -d --build

# 3. Chạy các kịch bản test tự động
python test_lb_basic.py -r 20                             # Kịch bản 1: Test tỷ lệ chia đều traffic 50-50
python test_lb_failover.py -r 15                          # Kịch bản 2: Test tự động bẻ lái khi tắt nóng 1 server
python test_lb_stress.py -d 30 -t 3 -r 5                  # Kịch bản 3: Ép xung hệ thống, đo thời gian phản hồi
python test_lb_advanced_failover.py -d 30 -t 3 -r 5       # Kịch bản 4: Test tổng hợp (ngắt kết nối + DDOS)

# 4. Xem báo cáo kết quả chi tiết (Được tự động sinh ra sau khi chạy test)
cat stress_test_report_*.json
cat failover_report_*.json

# 5. [Tính mới] Áp dụng Rate limit
* Mở lệnh dòng 10 và 28 ở file `nginx.conf`
docker-compose restart                      # Khởi động lại docker
python test_lb_stress.py -d 10 -t 5 -r 10   # Ép 5 luồng, mỗi luồng 10 request/s => Tổng dội vào 50 request/giây

# 6. Dọn dẹp tài nguyên sau khi hoàn thành Demo
docker-compose down
```
