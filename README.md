# Đồ án: Triển khai Cân bằng tải Web (Web Load Balancing) với Nginx

**Sinh viên thực hiện:** Vũ Thiên Trường (MSSV: 2001231015) - Nhóm [Điền tên nhóm vào đây]

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