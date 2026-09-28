# Chi Tiết Task - K4 Level 3A (Ngày 12)
**Bài lab:** Hạ Tầng Cloud & Deployment

Tài liệu này tóm tắt các yêu cầu và công việc phải làm từ các file `.md` trong dự án `K4-L3A-DAY12-NguyenDuyKhanh-2A202602736-CloudServicesAndDeployment`. Mục tiêu của bài là cấu hình và triển khai (deploy) một AI agent lên nền tảng cloud công khai với khả năng bảo mật, giới hạn tài nguyên và tính ổn định tốt.

---

## 1. Quy định chung & Nộp bài
- **Bài làm cá nhân:** Không chia sẻ code hoặc repo, có thể thảo luận cách làm. 
- **Tên repo bắt buộc:** `K4-L3A-DAY12-<HoVaTen>-<MSSV>-CloudServicesAndDeployment` (sai trừ 5 điểm).
- **Bảo mật:** Không được commit file `.env`, mật khẩu, secret keys vào repo (nếu có sẽ bị trừ 10 điểm). Các key này phải dùng thông qua Environment Variables của Cloud.
- **Nộp bài:** Hoàn thiện `exercises.md`, `DEPLOYMENT.md`, cấp link repo (public domain) kèm các screenshots cần thiết.

---

## 2. Chi tiết các Checkpoint (Công việc cần làm) và Mục đích

### CP0 — Setup (Môi trường & Chuẩn bị)
- **Công việc:**
  1. Đổi tên repo đúng cú pháp quy định.
  2. Tạo môi trường ảo python (`venv`) và cài đặt các thư viện trong `requirements.txt`.
  3. Tạo file `.env` từ `.env.example`, điền `AGENT_API_KEY` (tạo ngẫu nhiên bằng lệnh python).
  4. Khởi động cấu hình Redis bằng Docker (`docker compose up -d redis`).
- **Mục đích:** Thiết lập môi trường chạy thử và các dependencies bắt buộc ban đầu để code có thể hoạt động ở nội bộ (localhost).

### CP1 — 12-Factor Config, Health & Logging (Cấu trúc & Giám sát)
- **Công việc:**
  1. `app/config.py`: Khai báo 6 biến cấu hình, đảm bảo biến `agent_api_key` **không có giá trị mặc định**.
  2. `app/logging_utils.py`: Chỉnh sửa hàm log sao cho ghi dữ liệu dưới dạng JSON (mỗi lượt là một dòng JSON duy nhất, không xuống dòng bừa bãi).
  3. `app/main.py`: Viết API `/health` trả về liveness probe (chỉ phản ánh trạng thái API, không phụ thuộc vào trạng thái của Redis hay service thứ ba khác).
- **Mục đích:**
  - **12-Factor:** Tách biệt cấu hình khỏi code (để dễ dàng tuỳ biến biến môi trường khi đưa lên cloud). Nếu thiếu key, app sẽ báo lỗi ngay lập tức (fail fast) thay vì mặc định bỏ qua.
  - **Logging & Health:** Đảm bảo hệ thống có thể cung cấp log chuẩn hỗ trợ tracking và báo cáo trạng thái "còn sống" để orchestrator (chẳng hạn Docker/Cloud) có thể khởi động lại app kịp thời khi lỗi. 

### CP2 — Docker (Container hoá ứng dụng)
- **Công việc:**
  1. `Dockerfile`: Sửa theo hướng dẫn multi-stage (để giảm dung lượng image), đặt `COPY` code xuống cuối để tận dụng Docker cache, tạo non-root user `appuser` để ứng dụng không chạy quyền cao nhất, thêm cấu hình đọc port động cấu hình Cloud cung cấp, và thiết lập `HEALTHCHECK`.
  2. `.dockerignore`: Chặn đưa lộ `__pycache__`, `.venv`, `.env` vào image build.
  3. `docker-compose.yml`: Bổ sung thêm service `agent` đọc biến từ `.env`, phụ thuộc (`depends_on`) vào redis.
- **Mục đích:** Đóng gói ứng dụng thành một image gọn nhẹ, bảo mật, và có khả năng mang đi chạy ổn định không lỗi lệch môi trường trên bất cứ nền tảng server nào.

### CP3 — API Security (Bảo mật, Giới hạn Request & Cost Guard)
- **Công việc:**
  1. `app/auth.py`: Bổ sung kiểm tra header `X-API-Key` so sánh với `agent_api_key` trong hệ thống (dùng hàm `secrets.compare_digest` để tránh tấn công timing attack).
  2. `app/rate_limiter.py`: Xây dựng thuật toán Cửa sổ trượt (Sliding Window) qua Redis Sorted Set (ZSET) với khoá và timestamp duy nhất để ngăn spam gửi API.
  3. `app/cost_guard.py`: Ghi lại chi phí token tiêu thụ, tổng hợp theo tháng của lượng tiền tệ. Chặn API (402) nếu tiêu quá quy định.
  4. `app/main.py`: Tuần tự hóa quy trình trước khi gọi vào LLM (Kiểm tra API Key -> Kiểm tra Rate Limit -> Kiểm tra Ngân Sách -> LLM Call -> Log).
- **Mục đích:** Cung cấp 3 lớp bảo vệ quan trọng ở tầng Cloud. Không cho kẻ lạ truy cập API trái phép, chặn đứng các đợt càn quét mạng bằng giới hạn tần suất gửi tin, và ngăn hoá đơn OpenAI/Cloud trượt dài do phá phách bot spam.

### CP4 — Scaling & Reliability (Stateless & Độ bền bỉ)
- **Công việc:**
  1. `app/store.py`: Tách lịch sử chat (message history) ra khỏi RAM của application, đẩy sang Redis (giới hạn tối đa số lượt giữ lại và thời gian lưu rác thông qua `ltrim` và `expire`). 
  2. `app/main.py`: Thiết lập endpoint `/ready` báo trạng thái sẵn sàng nhận traffic – bao gồm kiểm tra trạng thái hoạt động chéo qua Redis.
  3. `app/lifecycle.py`: Tích hợp Graceful Shutdown bắt tín hiệu (`SIGINT`/`SIGTERM`), đưa service nhường vòng lặp mà không ngắt đột ngột request đang dang dở từ người dùng.
- **Mục đích:** Cho phép Service có thể mở rộng (scale) ra làm thành nhiều containers (chạy ở nhiều server khác nhau) mà không gặp trường hợp mất dữ liệu chat (stateless). Ngắt khứ an toàn các requests khi cần cập nhật code, tránh bị người dùng bắt lỗi "502/503 Bad Gateway" khi deploy.

### CP5 — Cloud Deployment (Triển khai chính thức)
- **Công việc:**
  1. Deploy app (đã gói qua Dockerfile) lên một nền tảng Cloud (Railway, Render, v.v.).
  2. Cấu hình biến môi trường (`AGENT_API_KEY`, `REDIS_URL`, v.v.) bên trên dashboard của Cloud, không code cứng.
  3. Kiểm tra bằng `curl` công khai để đảm bảo route `/health`, `/ready` trả về chuẩn HTTP 200, trong khi `/ask` không gửi Key báo HTTP 401.
  4. Cập nhật Public URL và chứng minh trong file `DEPLOYMENT.md` và các ảnh trong `/screenshots/`.
- **Mục đích:** Chuyển hoá dịch vụ từ máy trạm localhost trở thành một hệ thống thực tế nằm trên internet công khai.

### Bonus Task — CI/CD với GitHub Actions (Không bắt buộc, +10 điểm)
- **Công việc:** Cấu hình file `.github/workflows/ci.yml` tự động chạy mỗi khi push code lên `main`. CI sẽ thực hiện chạy các bài Unit Test (`pytest`), kiểm tra Build Docker, và chỉ tự động CD (deploy lên Platform) khi mọi Test case đều xanh. Ngoài ra có thêm badge thông báo vào README.md.
- **Mục đích:** Triết lý tự động hóa. Đảm bảo mọi commit code đều vượt qua bài xét duyệt chất lượng trước khi thay thế bản trên Cloud.

### Phản ánh (exercises.md)
- **Công việc:** Điền câu trả lời giải thích vào 10 câu hỏi lý thuyết kèm ứng dụng trong `exercises.md`.
- **Mục đích:** Giúp giáo viên & Lab Coach kiểm tra hiểu biết thật sự của học viên đối với phần code mà học viên tự tay viết (Fail Fast xử lí ra sao, tại sao không chạy quyền root bằng Docker, và vì sao stateless lại quan trọng...).

---

## Hướng Dẫn Deploy CP5 Qua Nền Tảng Cloud (Render)

Sau khi bạn đã hoàn thiện CP2 (chuẩn hoá file `Dockerfile` thành multi-stage), project của bạn hiện đã hoàn toàn đóng gói cô lập. Tuyệt đối không thay đổi gốc các file `DEPLOYMENT.md` khi chưa deploy thành công hay dán secret vào repo.

#### Sử dụng Render.com (Build Blueprint Trực Tiếp Từ Github)
Nền tảng Render cho phép liên kết tài khoản Github để tự động kéo mã nguồn mới nhất và triển khai qua bộ `Dockerfile`. Bạn làm theo các bước sau:

1. **Chuẩn bị và Push source-code lên Github:**
   Commit những thay đổi mới nhất (đã chắn chắn loại bỏ file `.env` nhờ file `.gitignore`) và push lên Git branch chính (Tên repo đạt chuẩn: `K4-L3A-DAY12-HoVaTen-MSSV-CloudServicesAndDeployment`).

2. **Dựng Redis Host:**
   - Đăng nhập Dashboard của [Render](https://render.com).
   - Chọn tạo mới **New** -> **Redis**. Đặt tên cho instance mới của bạn và chọn Free/Hobby Tier tuỳ ý sau đó nhấn "Create Redis".
   - Sau khi khởi tạo xong, hãy copy lại chuỗi **Internal Redis URL**. (đây là URL dùng riêng trong mạng nội bộ của Render, có tốc độ kết nối cao nhất và an toàn mã hoá).

3. **Tạo và Cấu hình Web Service:**
   - Tại vị trí Dashboard [Render](https://render.com), chọn **New** -> **Web Service**.
   - Cấp quyền cho Render đọc Repository Github của bạn và chọn repo đồ án môn học để tiếp tục.
   - Tại các thông số Setup, điền Environment setting sang **Docker** (Thay cho Native / Buildpacks).
   - Ngay phía dưới, mục **Environment Variables**, chọn "Add Environment Variable" và điền thủ công các cặp giá trị sau (Tuyệt đối không sử dụng tệp `.env` file import vì tệp `.env` không được lưu trữ online):
     - `AGENT_API_KEY`: <Chuỗi khóa bảo mật của bạn đang dùng ở Local>
     - `RATE_LIMIT_PER_MINUTE`: 10
     - `MONTHLY_BUDGET_USD`: 10.0
     - `LOG_LEVEL`: INFO
     - `REDIS_URL`: <Dán giá trị chuỗi *Internal Redis URL* lấy được ở Bước 2>
   - *Lưu ý: Không set biến `PORT`, bởi hệ thống Render sẽ cung cấp tự động biến đó động học.*

4. **Deploy:**
   - Kéo xuống dưới cùng và chọn nút **Create Web Service**. Chờ Render tiến hành build images trực tiếp qua hệ thống Docker của họ và deploy (quy trình tải package lib và make stages sẽ mất khoảng ~3 phút).
   - Sau khi hoàn tất và Console báo dòng `Your service is live 🎉`, bạn sẽ nhận được một địa chỉ Web Service URL ngay dưới tên project (ví dụ: `your-project-xxx.onrender.com`).
   - Khi có địa chỉ public này, hãy dán thay thế vào thẻ `<URL>` bên dưới để tiến hành kiểm tra bảo mật API.

### Lệnh Kiểm Tra Cụ Thể (Liveness, Readiness, Rate-Limit & HTTP Auth)

**1. Kiểm tra Liveness: Agent đã up thành công chưa?**
```bash
curl -i <URL>/health
# Kết quả đúng: HTTP 200 OK + JSON
```

**2. Kiểm tra Readiness: Agent kết nối Redis chưa?**
```bash
curl -i <URL>/ready
# Kết quả đúng: HTTP 200 OK + JSON
```

**3. Kiểm tra Xác Thực: Block API nặc danh**
```bash
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'
# Kết quả báo: HTTP 401 Unauthorized
```

**4. Kiểm tra Spam (Rate Limiter CP3):**
```bash
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST <URL>/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: KHÓA_CỦA_BẠN" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test spam"}'
done; echo
# Phải xuất hiện lỗi Rate Limit HTTP 429 sau 10 query đầu.
```
