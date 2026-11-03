# Quy ước nhánh, commit message và PR

Tài liệu này thực hiện REQ-006. Mọi thay đổi vào repo cần tuân theo quy ước dưới đây.

## 1. Đặt tên nhánh

Định dạng:

```
<type>/<TASK-ID>-<mo-ta-ngan>
```

- `<type>`: một trong `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
- `<TASK-ID>`: mã task, dạng `TASK-` + 4 chữ số (ví dụ `TASK-0035`).
- `<mo-ta-ngan>`: chữ thường không dấu, các từ nối bằng dấu gạch ngang `-`.

Biểu thức chính quy: `^(feat|fix|docs|refactor|test|chore)/TASK-[0-9]{4}-[a-z0-9]+(-[a-z0-9]+)*$`

Ví dụ hợp lệ:

- `docs/TASK-0035-quy-uoc-nhanh-commit-pr`
- `feat/TASK-0012-dang-nhap`
- `fix/TASK-0101-sua-loi-timeout`

Ví dụ không hợp lệ:

- `my-branch` (thiếu type và TASK-ID)
- `feat/TASK-12-dang-nhap` (TASK-ID phải có 4 chữ số)
- `feat/TASK-0012-Dang_Nhap` (không dùng chữ hoa hoặc dấu gạch dưới)

## 2. Commit message

Theo kiểu Conventional Commits:

```
<type>(<TASK-ID>): <tóm tắt ngắn>

<mô tả chi tiết (tùy chọn)>

Refs: REQ-xxx
```

Quy tắc:

- `<type>` dùng cùng danh sách như nhánh.
- Dòng tiêu đề không quá 72 ký tự, không kết thúc bằng dấu chấm, viết ở thể mệnh lệnh.
- Dòng `Refs:` ghi các REQ liên quan (phân tách bằng dấu phẩy) khi có.
- Mỗi commit chỉ chứa một thay đổi có ý nghĩa.

Biểu thức chính quy cho dòng tiêu đề:
`^(feat|fix|docs|refactor|test|chore)\(TASK-[0-9]{4}\): .{1,72}$`

Ví dụ hợp lệ:

- `docs(TASK-0035): thêm quy ước nhánh, commit và mẫu PR`
- `feat(TASK-0012): thêm màn hình đăng nhập`
- `fix(TASK-0101): tăng timeout khi gọi dịch vụ`

Ví dụ không hợp lệ:

- `update stuff` (thiếu type và TASK-ID)
- `Fix: sửa lỗi.` (sai định dạng, có dấu chấm cuối)

## 3. Pull request

Khi tạo PR, GitHub tự điền mẫu từ `.github/pull_request_template.md`. Người tạo cần điền:

1. **Mô tả**: thay đổi gì và vì sao.
2. **REQ / Task liên quan**: mã REQ và TASK.
3. **Cách test**: lệnh đã chạy, các bước kiểm tra thủ công, kết quả.
4. **Checklist**: xác nhận tên nhánh, commit và test đúng quy ước.

Tiêu đề PR dùng cùng định dạng với dòng tiêu đề commit.

## 4. Kiểm tra tự động

Chạy `sh backend/tests/check_conventions.sh` để kiểm tra tài liệu và mẫu PR có đủ nội dung bắt buộc, và các ví dụ khớp biểu thức chính quy.
