<p align="center">
  <strong>GitHub Manager</strong>
</p>
<p align="center">
  Ứng dụng desktop Windows quản lý tài khoản GitHub bằng PAT, commit & push từng file vào <code>uploads/</code> — một commit, một push cho mỗi file.
</p>

---

## 📋 Mục lục

- [Yêu cầu](#-yêu-cầu)
- [Cài đặt](#-cài-đặt)
- [Chạy ứng dụng](#-chạy-ứng-dụng)
- [Build file .exe](#-build-file-exe)
- [Tính năng](#-tính-năng)
- [Vị trí dữ liệu](#-vị-trí-dữ-liệu)
- [Xóa dữ liệu / Reset](#-xóa-dữ-liệu--reset)

---

## 🔧 Yêu cầu

| Thành phần | Phiên bản / Ghi chú |
|------------|---------------------|
| **Python** | 3.11 trở lên |
| **Hệ điều hành** | Windows (dùng `%LOCALAPPDATA%` và Windows Credential Manager) |
| **Git** | Cài sẵn và có trong `PATH` (để clone, commit, push) |

---

## 📦 Cài đặt

**1. Vào thư mục dự án**

```bash
cd github_manager
```

**2. Tạo môi trường ảo (nên dùng)**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**3. Cài dependency**

```bash
pip install -r requirements.txt
```

Hoặc double-click file **`install_requirements.bat`** (trong thư mục `github_manager`).

---

## ▶️ Chạy ứng dụng

Trong thư mục `github_manager`:

```bash
python app.py
```

---

## 📤 Build file .exe

**Bước 1:** Tạo icon (logo GitHub Octocat) cho file .exe:

```bash
cd github_manager
pip install Pillow requests
python build_icon.py
```

→ Tạo file `assets/icon.ico`.

**Bước 2:** Build một file .exe, không console, có icon:

```bash
pyinstaller GitHubManager.spec
```

Hoặc không dùng spec:

```bash
pyinstaller --noconsole --onefile --name GitHubManager --icon=assets/icon.ico app.py
```

- **Kết quả:** `dist\GitHubManager.exe` (icon con mèo GitHub, khi chạy có phiên bản và link repo trong **Help → About**).

---

## ✨ Tính năng

| Trang | Mô tả |
|-------|--------|
| **Accounts** | Thêm tài khoản bằng PAT (Fine-grained hoặc Classic), lưu token vào Windows Credential Manager. Kiểm tra PAT còn hạn, xóa tài khoản khi không dùng nữa. |
| **Repositories** | Chọn tài khoản, tải danh sách repo (tên đầy đủ, Public/Private, nhánh mặc định). |
| **Commit & Push** | Chọn tài khoản → repo → nhánh → nhiều file. Mỗi file được commit vào `uploads/<tên_file>` (tên an toàn, trùng thì đánh số), **một commit + một push** cho từng file. |
| **Runs / Logs** | Xem lịch sử chạy và đường dẫn file log. |

- **Bảo mật:** Không dùng username/password; chỉ PAT. Token không lưu trong file JSON.
- **Luồng xử lý:** Git chạy nền, giao diện không bị treo.
- **Phiên bản & link:** Cửa sổ hiển thị version (vd. v1.0.0); menu **Help → About** có link tới [GitHub project](https://github.com/TroLyAmazon/GitHub-Manager).

---

## 📁 Vị trí dữ liệu

Mọi dữ liệu nằm trong:

```
%LOCALAPPDATA%\GitHubManager\
```

| Thư mục / File | Nội dung |
|----------------|----------|
| `data\accounts.json` | Metadata tài khoản (label, login, secretKey tham chiếu — **không** chứa token). |
| `data\runs.json` | Lịch sử các lần commit/push. |
| `logs\` | File log chi tiết từng lần chạy. |
| `workspaces\<accountId>\<owner_repo>\` | Bản clone repo và thư mục `uploads\`. |

Token (PAT) được lưu trong **Windows Credential Manager** qua thư viện `keyring`.

---

## 🗑️ Xóa dữ liệu / Reset

Khi không dùng app nữa hoặc muốn reset:

1. **Xóa dữ liệu app** (thư mục, data, logs, workspaces):  
   Chạy **`xoa_du_lieu_app.bat`**.

2. **Xóa token khỏi Windows** (PAT đã lưu):  
   Chạy **`xoa_tai_khoan_windows.bat`**.

Hai file `.bat` nằm trong thư mục `github_manager`. Nhớ đóng app trước khi xóa.

---

## 📄 Giấy phép & Đóng góp

Dự án mở. Bạn có thể chỉnh sửa và dùng theo nhu cầu.
