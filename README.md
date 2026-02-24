# Đồ án: Triển khai Cân bằng tải Web (Web Load Balancing) với Nginx

**Nhóm thực hiện:** 16 [BonChangLinhNguLam] 

---

## 📌 Giới thiệu dự án
Dự án này mô phỏng một hệ thống phân phối tải truy cập (Load Balancing) sử dụng Nginx đứng trước 2 Web Server riêng biệt. 

Điểm nổi bật của Demo này là hệ thống KHÔNG sử dụng thuật toán chia tải (Round-Robin) cơ bản, mà được thiết lập theo mô hình **Active - Backup** sát với cấu trúc thực tế của doanh nghiệp:
* **WEB1 (Server Chính):** Gánh toàn bộ traffic mặc định. Được cấu hình giới hạn sức chịu đựng tối đa 5 kết nối cùng lúc (`max_conns=5`).
* **WEB2 (Server Dự phòng):** Nằm ở trạng thái ngủ đông (`backup`). Trình quản lý Nginx sẽ chỉ "đánh thức" WEB2 để tiếp khách trong 2 trường hợp khẩn cấp:
  1. **Tràn tải (Spillover):** Khi WEB1 đạt ngưỡng giới hạn 5 khách.
  2. **Sự cố (Failover):** Khi WEB1 bị chết/sập nguồn đột ngột. Hệ thống đảm bảo tính sẵn sàng cao (HA), khách hàng không bị lỗi gián đoạn dịch vụ.

---

## 🛠 Phần mềm yêu cầu
Để chạy được bản Demo này, máy tính của bạn cần cài đặt sẵn:
1. **Docker Desktop:** Để ảo hóa và chạy các dịch vụ (Nginx, Web1, Web2) dưới dạng Container.
2. **Visual Studio Code (VS Code):** Môi trường viết code và chạy Terminal tích hợp để quan sát Log hệ thống.

---

## 🚀 Hướng dẫn khởi chạy và Demo

### Bước 1: Khởi động hệ thống
Mở thư mục chứa source code bằng VS Code. Mở Terminal lên (nhấn `Ctrl + \``) và gõ lệnh sau để dựng toàn bộ hệ thống ở chế độ chạy ngầm:

```bash
docker-compose up -d
```
*Lúc này, bạn có thể truy cập `http://localhost:8008` trên trình duyệt để thấy WEB1 đang hoạt động.*

### Bước 2: Thiết lập màn hình giám sát (Log)
Để thấy rõ Nginx chia tải thông minh như thế nào, hãy mở **2 Tab Terminal** mới trong VS Code (bấm dấu `+` trên khu vực Terminal) và chạy lần lượt các lệnh sau để theo dõi Log thời gian thực:

* **Tab Terminal 1 (Theo dõi WEB1):** ```bash
docker logs -f web1
```

* **Tab Terminal 2 (Theo dõi WEB2):** ```bash
docker logs -f web2
```

### Bước 3: Thực hiện các Kịch bản kiểm thử (Test Cases)

**Kịch bản 1: Giả lập tấn công / Tràn tải (Spillover)**
Mở thêm 1 Tab Terminal thứ 3 và sử dụng công cụ `wrk` (chạy qua Docker) để bắn 50 kết nối cùng lúc vào hệ thống trong 10 giây:

```bash
docker run --rm williamyeh/wrk -t2 -c50 -d10s http://host.docker.internal:8008/
```
👉 *Kết quả quan sát:* WEB1 sẽ chạy log cho 5 kết nối đầu tiên. Tab log của WEB2 sẽ lập tức nhảy liên tục để gánh phần traffic bị dội ra từ WEB1 do quá tải.

**Kịch bản 2: Giả lập sự cố sập máy chủ (Failover)**
Trong lúc hệ thống đang chạy bình thường, tiến hành "rút phích cắm" tắt nóng WEB1 bằng lệnh:

```bash
docker stop web1
```
👉 *Kết quả quan sát:* Nginx phát hiện WEB1 ngưng hoạt động và lập tức đẩy 100% traffic sang WEB2. Dịch vụ web vẫn truy cập bình thường không báo lỗi, trang web tự động chuyển sang hiển thị nội dung của WEB2.

### Bước 4: Khôi phục và Dọn dẹp hệ thống
* Để bật lại WEB1 (hồi sinh server): 
```bash
docker start web1
```

* Sau khi Demo xong, dùng lệnh sau để tắt và xóa toàn bộ các container, trả lại tài nguyên cho máy:
```bash
docker-compose down
```