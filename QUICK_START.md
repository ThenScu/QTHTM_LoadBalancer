# 🚀 Quick Start - Load Balancer Testing Suite

## 📦 Bạn Vừa Nhận Được

### 4 Python Scripts Chuyên Nghiệp
```
test_lb_basic.py          → Test cơ bản load balancing
test_lb_failover.py       → Test failover & recovery  
test_lb_stress.py         → Stress test & performance
test_lb_security.py       → Penetration testing
```

---

## 🚀 Bây Giờ Phải Chạy (4 Bước)

### BƯỚC 1: Mở Terminal
```cmd
cd d:\code\Nam3_HK2_25-26\QTHTM\nginx-load-balancer
```

### BƯỚC 2: Install Package
```bash
pip install requests
```

### BƯỚC 3: Khởi Động Docker
```bash
docker-compose up -d
```

### BƯỚC 4: Chạy Test Đầu Tiên
```bash
python test_lb_basic.py -r 20
```

---

## � Kết Quả Mong Đợi

```
[TEST 1] Checking Load Balancer Connectivity...
[OK] Load Balancer is responding

[TEST 2] Testing Load Distribution (20 requests)...
Request  1 -> WEB1 (5.5ms)
Request  2 -> WEB2 (4.3ms)
...

==================================================
TEST RESULTS
==================================================
Distribution:
  WEB1: 10 requests (50.0%)
  WEB2: 10 requests (50.0%)
  Failed: 0 requests

Response Times (ms):
  Average: 12.88
  Min:     3.46
  Max:     33.87

==================================================
[SUCCESS] Load balancing is working properly!
==================================================
```

---

## 🎯 3 Bước Tiếp Theo

### Bước 1: Basic Test (5 phút)
```bash
python test_lb_basic.py -r 20
```
→ Kiểm tra load balancing hoạt động

### Bước 2: Failover Test (10 phút)
```bash
python test_lb_failover.py -r 15
```
→ Kiểm tra automatic failover

### Bước 3: Stress & Security Test (15 phút)
```bash
python test_lb_stress.py -d 60
python test_lb_security.py
```
→ Performance metrics & security findings

### Khi Xong
```bash
docker-compose down
```

---

## � File Nào Đọc Trước?

### 🔴 MUST (Bắt buộc)
1. **START_HERE.txt** - File này
2. **QUICK_START.md** - Hướng dẫn chi tiết

### 🟡 SHOULD (Nên)
3. Script comments - Hiểu code từng script

### � OPTIONAL (Tùy)
4. **NGINX_QUICK_REFERENCE.txt** - Nginx config changes
5. **NGINX_CONFIG_CHANGES.md** - Chi tiết config

---

## ✨ Điểm Nổi Bật

### 1. Tự động hóa hoàn toàn
- Containers tự khởi động
- Tests tự chạy
- Reports tự tạo

### 2. Chi tiết và chuyên nghiệp
- Performance metrics (P95, P99)
- Real-time progress indicator
- Security findings analysis

---

## 🎊 Bạn Sẵn Sàng Rồi!

```
✅ Cài đặt: pip install requests
✅ Khởi động: docker-compose up -d
✅ Chạy: python test_lb_basic.py
✅ Thành công! 🎉
```

---

## 📞 Quick Commands Cheatsheet

```powershell
# Install once
pip install requests

# Start Docker
docker-compose up -d

# Run tests
python test_lb_basic.py -r 20
python test_lb_failover.py -r 15
python test_lb_stress.py -d 30 -t 3 -r 5
python test_lb_security.py

# View reports
cat stress_test_report_*.json
cat failover_report_*.json
cat security_findings_*.json

# Stop
docker-compose down
```

---

**Created**: 2026-03-27 | **Version**: 1.0 | **Python**: 3.7+
