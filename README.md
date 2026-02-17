<p align="center">
  <strong>GitHub Manager</strong>
</p>
<p align="center">
  Ứng dụng desktop Windows quản lý tài khoản GitHub bằng PAT, commit & push từng file vào <code>uploads/</code> — một commit, một push cho mỗi file.
</p>

---

## 📋 Mục lục

- [Cách chạy](#-cách-chạy)
- [Yêu cầu](#-yêu-cầu)
- [Tính năng](#-tính-năng)
- [Vị trí dữ liệu](#-vị-trí-dữ-liệu)
- [Xóa dữ liệu / Reset](#-xóa-dữ-liệu--reset)
- [Giấy phép & Đóng góp](#-giấy-phép--đóng-góp)

---

## ▶️ Cách chạy

1. **Tải file cài đặt** (bản mới nhất):
   - [**Download GitHub.Manager.V1.1.2.exe**](https://github.com/TroLyAmazon/GitHub-Manager/releases/download/V1.1.2/GitHub.Manager.V1.1.2.exe)
2. Mở file **`.exe`** vừa tải và chạy như ứng dụng Windows thông thường.

Không cần cài Python hay build gì thêm — chỉ cần tải và chạy.

---

## 🔧 Yêu cầu

| Thành phần | Ghi chú |
|------------|---------|
| **Hệ điều hành** | Windows (dùng `%LOCALAPPDATA%` và Windows Credential Manager) |
| **Git** | Cài sẵn và có trong `PATH` (để clone, commit, push) |

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
   Xóa toàn bộ thư mục: `%LOCALAPPDATA%\GitHubManager\`  
   (Nhớ đóng app trước khi xóa.)

2. **Xóa token khỏi Windows** (PAT đã lưu):  
   Mở **Windows Credential Manager** → **Windows Credentials** → tìm và xóa các mục liên quan **GitHubManager**.

---

## 📄 Giấy phép & Đóng góp

Dự án **miễn phí**, mở mã nguồn. Bạn có thể dùng, chỉnh sửa và đóng góp theo nhu cầu.  
**Vui lòng không bán** phần mềm này — hãy giữ nó free cho cộng đồng.
