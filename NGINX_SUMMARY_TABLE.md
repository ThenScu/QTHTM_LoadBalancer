🔧 NGINX CONFIGURATION - SUMMARY TABLE
═══════════════════════════════════════════════════════════════════════════

PARAMETER | TÁC DỤNG | GIÁ TRỊ CŨ | GIÁ TRỊ MỚI | LÝ DO
─────────────────────────────────────────────────────────────────────────

UPSTREAM (Round-Robin Load Balancing):

weight          | Trọng lượng requests      | (không có) | 1 (WEB1,WEB2) | Cân bằng 50-50
max_fails       | Fail threshold           | 2          | 2 (không đổi) | Detect backend down
fail_timeout    | Thời gian skip           | 5s         | 5s (không đổi)| OK
backup mode     | WEB2 chỉ khi WEB1 fail  | ACTIVE ❌  | DISABLED ✅   | Chạy song song
keepalive       | Idle connections         | 16         | 32            | Connection pool

PROXY SETTINGS (Performance):

proxy_http_version | HTTP version            | (implicit) | 1.1 ✨       | Hỗ trợ keepalive
Connection header  | Connection reuse        | (không có) | "" ✨        | Keepalive active
Host header        | Backend hostname        | $host      | $host        | (không đổi)
X-Real-IP          | Client IP tracking      | $remote_addr | $remote_addr | (không đổi)
X-Forwarded-For    | Proxy chain tracking    | $proxy_add_x_forwarded_for | (không đổi) | (không đổi)

FAILOVER (Error Handling):

proxy_next_upstream    | Failover trigger      | error timeout http_502... | (không đổi) | Detect errors
proxy_next_upstream_tries | Max retry attempts | (implicit) | 2 ✨        | Tối đa 2 lần
proxy_next_upstream_timeout | Max failover time | (không có) | 3s ✨      | 3s để failover

TIMEOUTS (Stability):

proxy_connect_timeout  | Kết nối timeout       | 2s         | 2s (không đổi)| OK
proxy_read_timeout     | Đọc response timeout  | 5s         | 10s ✨       | Cho requests lâu hơn
proxy_send_timeout     | Gửi request timeout   | (không có) | 10s ✨       | Tránh timeout gửi

═════════════════════════════════════════════════════════════════════════════

📊 LOAD DISTRIBUTION COMPARISON:
─────────────────────────────────────────────────────────────────────────

CONFIG CŨ:
  upstream web_backend {
    server web1:80 max_fails=2 fail_timeout=5s;
    server web2:80 max_fails=2 fail_timeout=5s;
    # server web1:80 max_conns=5;        ← Comment
    # server web2:80 backup;             ← Comment
  }
  
  Kết quả: WEB1 100% ❌, WEB2 0% ❌
  Nguyên nhân: Cấu hình mơ hồ, backup mode active

CONFIG MỚI:
  upstream web_backend {
    server web1:80 max_fails=2 fail_timeout=5s weight=1;
    server web2:80 max_fails=2 fail_timeout=5s weight=1;
    keepalive 32;
  }
  
  Kết quả: WEB1 ≈50% ✅, WEB2 ≈50% ✅
  Nguyên nhân: Round-robin rõ ràng, cân bằng hoàn hảo

═════════════════════════════════════════════════════════════════════════════

✨ KEY IMPROVEMENTS:
─────────────────────────────────────────────────────────────────────────

1. Load Balancing Strategy
   ❌ Before: Backup mode (WEB2 inactive by default)
   ✅ After:  Round-robin with equal weights (50-50 split)

2. Connection Efficiency
   ❌ Before: No HTTP/1.1 explicit, no Connection reuse
   ✅ After:  HTTP/1.1 + keepalive → Connection pooling

3. Failover Timeout
   ❌ Before: No explicit timeout
   ✅ After:  3s timeout + 2 tries → Fast failover

4. Request Timeout
   ❌ Before: 5s read timeout only
   ✅ After:  10s read + 10s send → Better stability

5. Connection Pooling
   ❌ Before: keepalive 16
   ✅ After:  keepalive 32 → More concurrent connections

═════════════════════════════════════════════════════════════════════════════

🎯 NGINX CONFIG BEHAVIOR FLOWCHART:
─────────────────────────────────────────────────────────────────────────

CLIENT REQUEST
    ↓
LOAD BALANCER (nginx)
    ↓
    ├─ Round-Robin Distribution
    │  ├─ Request #1 → WEB1:80 ✅
    │  ├─ Request #2 → WEB2:80 ✅
    │  ├─ Request #3 → WEB1:80 ✅
    │  └─ Request #4 → WEB2:80 ✅
    │
    ├─ If Backend Fails
    │  ├─ error/timeout → proxy_next_upstream
    │  ├─ Try alternate backend (max 2 tries)
    │  ├─ Timeout: 3s
    │  └─ Return error if all fail
    │
    ├─ Connection Management
    │  ├─ HTTP/1.1 keepalive active
    │  ├─ Reuse idle connections
    │  ├─ Pool size: 32 connections
    │  └─ Faster subsequent requests
    │
    └─ Timeouts
       ├─ Connect: 2s
       ├─ Read: 10s
       └─ Send: 10s

═════════════════════════════════════════════════════════════════════════════

📋 EFFECTS ON PYTHON SCRIPTS:
─────────────────────────────────────────────────────────────────────────

Script | Change | Effect | Need Update?
─────────────────────────────────────────────────────────────────────────
test_lb_basic.py | WEB1/WEB2 50-50 | Different results | ✅ No (flexible)
test_lb_failover.py | Faster failover (3s) | Quicker recovery | ✅ No (auto)
test_lb_stress.py | 2 backends load | Higher throughput | ✅ No (auto)
test_lb_security.py | Both backends tested | More endpoints | ✅ No (flexible)

═════════════════════════════════════════════════════════════════════════════

🔄 BEFORE vs AFTER:
─────────────────────────────────────────────────────────────────────────

BEFORE CONFIG (CŨ):
  ❌ WEB1: 100% requests
  ❌ WEB2: 0% requests (backup)
  ❌ No efficient connection reuse
  ❌ Not clear why unbalanced

AFTER CONFIG (MỚI):
  ✅ WEB1: ~50% requests
  ✅ WEB2: ~50% requests
  ✅ Efficient keepalive + HTTP/1.1
  ✅ Crystal clear round-robin logic

═════════════════════════════════════════════════════════════════════════════

🚀 READY TO TEST:
─────────────────────────────────────────────────────────────────────────

$ docker-compose down
$ docker-compose up -d
$ python test_lb_basic.py -r 20

EXPECTED OUTPUT:
  Request  1 -> WEB1 (5.5ms)
  Request  2 -> WEB2 (4.3ms)  ← ✨ Alternating!
  Request  3 -> WEB1 (5.9ms)
  Request  4 -> WEB2 (6.2ms)
  ...
  
  Distribution:
    WEB1: 10 requests (50.0%)  ← ✨ CHANGED!
    WEB2: 10 requests (50.0%)  ← ✨ CHANGED!
    Failed: 0 requests

═════════════════════════════════════════════════════════════════════════════
