# 🚀 Quick Start - Load Balancer Testing Suite

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
python test_lb_advanced_failover.py -d 30 -t 3 -r 5

# View reports
cat stress_test_report_*.json
cat failover_report_*.json
cat security_findings_*.json

# Stop
docker-compose down
```

---

| **Version**: 1.0 | **Python**: 3.7+
