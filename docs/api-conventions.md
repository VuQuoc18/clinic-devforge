# Quy ước API

Trạng thái: **Bản nháp – chờ Tech lead review** (TASK-0036, REQ-007)

Áp dụng cho mọi API mới. API cũ không bắt buộc đổi trừ khi có task riêng.

> ⚠️ **CHỜ XÁC NHẬN – DEC-0001 (Câu hỏi mở): ngôn ngữ mã lỗi và thông điệp lỗi.**
> Chưa có kết quả xác nhận, nên tài liệu dùng **giả định tạm** sau:
>
> - `code`: tiếng Anh, `UPPER_SNAKE_CASE`, ổn định, dành cho máy đọc. Không dịch.
> - `message`: tiếng Anh, dành cho lập trình viên (log, debug). Client tự hiển thị
>   thông điệp cho người dùng cuối (bản địa hóa) dựa trên `code`.
>
> Khi DEC-0001 được xác nhận, cập nhật mục này và các ví dụ trong mục 1.
> Vì client phụ thuộc vào `code` chứ không phải `message`, đổi ngôn ngữ `message`
> không phá vỡ tương thích.

---

## 1. Định dạng lỗi

### 1.1 Quy tắc

- Mọi phản hồi lỗi (HTTP 4xx/5xx) dùng cùng một cấu trúc JSON, `Content-Type: application/json`.
- Dùng HTTP status đúng ngữ nghĩa; không trả `200` kèm lỗi trong body.
- Cấu trúc:

| Trường | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `error.code` | string | có | Mã lỗi ổn định, `UPPER_SNAKE_CASE` (ngôn ngữ: chờ DEC-0001, tạm là tiếng Anh) |
| `error.message` | string | có | Mô tả cho lập trình viên (ngôn ngữ: chờ DEC-0001, tạm là tiếng Anh) |
| `error.details` | array | không | Chi tiết theo trường, dùng cho lỗi validate |
| `error.details[].field` | string | có (trong details) | Tên trường lỗi, dạng `snake_case`; trường lồng nhau dùng dấu chấm, ví dụ `address.city` |
| `error.details[].code` | string | có (trong details) | Mã lỗi của trường |
| `error.details[].message` | string | có (trong details) | Mô tả lỗi của trường |
| `error.request_id` | string | có | Mã truy vết, trùng header `X-Request-Id` |

- Không đưa stack trace, câu SQL hay thông tin nội bộ vào phản hồi.

### 1.2 Bảng mã lỗi chung

| HTTP | `code` | Khi nào dùng |
|---|---|---|
| 400 | `INVALID_REQUEST` | Body/tham số sai định dạng |
| 401 | `UNAUTHENTICATED` | Thiếu hoặc sai thông tin xác thực |
| 403 | `FORBIDDEN` | Đã xác thực nhưng không đủ quyền |
| 404 | `RESOURCE_NOT_FOUND` | Không tìm thấy tài nguyên |
| 409 | `CONFLICT` | Xung đột trạng thái (ví dụ trùng dữ liệu duy nhất) |
| 422 | `VALIDATION_FAILED` | Dữ liệu đúng định dạng nhưng sai nghiệp vụ/ràng buộc |
| 429 | `RATE_LIMITED` | Vượt giới hạn tần suất |
| 500 | `INTERNAL_ERROR` | Lỗi không mong đợi phía server |

Mã lỗi nghiệp vụ riêng đặt theo dạng `<DOMAIN>_<REASON>`, ví dụ `ORDER_ALREADY_PAID`.

### 1.3 Ví dụ

Lỗi validate:

```http
POST /v1/users HTTP/1.1
Content-Type: application/json

{ "email": "abc", "full_name": "" }
```

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
X-Request-Id: req_8f3a21

{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Request validation failed.",
    "details": [
      { "field": "email", "code": "INVALID_FORMAT", "message": "Email is not a valid address." },
      { "field": "full_name", "code": "REQUIRED", "message": "Full name must not be empty." }
    ],
    "request_id": "req_8f3a21"
  }
}
```

Không tìm thấy tài nguyên:

```http
GET /v1/users/9999 HTTP/1.1
```

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User 9999 was not found.",
    "request_id": "req_91bc07"
  }
}
```

---

## 2. Phân trang

### 2.1 Quy tắc

- Mọi endpoint trả danh sách đều phân trang; không trả toàn bộ dữ liệu không giới hạn.
- Dùng **phân trang theo offset** với tham số query:

| Tham số | Mặc định | Ràng buộc | Mô tả |
|---|---|---|---|
| `page` | `1` | số nguyên ≥ 1 | Số trang (bắt đầu từ 1) |
| `page_size` | `20` | 1–100 | Số phần tử mỗi trang |
| `sort` | tùy endpoint | — | Tên trường; tiền tố `-` là giảm dần, ví dụ `-created_at` |

- Giá trị ngoài ràng buộc trả `400` với `code = INVALID_REQUEST`; không tự điều chỉnh âm thầm.
- Phản hồi có `data` (mảng) và `pagination`:

| Trường | Mô tả |
|---|---|
| `pagination.page` | Trang hiện tại |
| `pagination.page_size` | Kích thước trang áp dụng |
| `pagination.total_items` | Tổng số phần tử khớp điều kiện |
| `pagination.total_pages` | Tổng số trang (`0` nếu không có phần tử) |

- Trang vượt quá `total_pages` trả `200` với `data: []`.
- Với tập dữ liệu rất lớn hoặc thay đổi liên tục, có thể dùng cursor (`cursor`, `next_cursor`)
  nhưng phải được tech lead đồng ý riêng.

### 2.2 Ví dụ

```http
GET /v1/orders?page=2&page_size=2&sort=-created_at HTTP/1.1
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": [
    { "id": "ord_103", "status": "paid", "created_at": "2024-05-02T09:15:00Z" },
    { "id": "ord_102", "status": "pending", "created_at": "2024-05-01T17:40:00Z" }
  ],
  "pagination": {
    "page": 2,
    "page_size": 2,
    "total_items": 5,
    "total_pages": 3
  }
}
```

Tham số không hợp lệ:

```http
GET /v1/orders?page=0&page_size=500 HTTP/1.1
```

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid pagination parameters.",
    "details": [
      { "field": "page", "code": "OUT_OF_RANGE", "message": "page must be >= 1." },
      { "field": "page_size", "code": "OUT_OF_RANGE", "message": "page_size must be between 1 and 100." }
    ],
    "request_id": "req_a1d4e5"
  }
}
```

---

## 3. Đặt tên route

### 3.1 Quy tắc

1. Có tiền tố phiên bản: `/v1/...`. Thay đổi phá vỡ tương thích thì tăng phiên bản.
2. Tên tài nguyên là **danh từ số nhiều**, chữ thường, nhiều từ nối bằng dấu gạch ngang (`kebab-case`):
   `/v1/order-items`.
3. Không dùng động từ trong đường dẫn; hành vi biểu diễn bằng HTTP method.
4. Định danh tài nguyên ở path: `/v1/orders/{order_id}`. Tên tham số path dùng `snake_case`.
5. Quan hệ lồng nhau tối đa 2 cấp: `/v1/orders/{order_id}/items`. Sâu hơn thì tách thành route cấp cao nhất.
6. Tham số query và trường JSON dùng `snake_case`.
7. Không có dấu `/` ở cuối; không dùng phần mở rộng như `.json`.
8. Hành động không phù hợp CRUD là ngoại lệ: dùng `POST` tới sub-resource động từ
   `/v1/orders/{order_id}/cancel`.

| Hành vi | Method | Route | Thành công |
|---|---|---|---|
| Liệt kê | `GET` | `/v1/orders` | `200` |
| Xem chi tiết | `GET` | `/v1/orders/{order_id}` | `200` |
| Tạo | `POST` | `/v1/orders` | `201` + header `Location` |
| Thay thế toàn bộ | `PUT` | `/v1/orders/{order_id}` | `200` |
| Cập nhật một phần | `PATCH` | `/v1/orders/{order_id}` | `200` |
| Xóa | `DELETE` | `/v1/orders/{order_id}` | `204` |
| Hành động đặc biệt | `POST` | `/v1/orders/{order_id}/cancel` | `200` |

### 3.2 Ví dụ

Đúng / sai:

| Nên dùng | Không nên dùng | Lý do |
|---|---|---|
| `GET /v1/order-items` | `GET /v1/getOrderItems` | Động từ, camelCase |
| `GET /v1/users/{user_id}` | `GET /v1/user/{userId}` | Số ít, camelCase |
| `GET /v1/orders/{order_id}/items` | `GET /v1/orders/{order_id}/items/{item_id}/options/{option_id}/values` | Lồng quá 2 cấp |
| `POST /v1/orders` | `POST /v1/orders/create` | Động từ trong path |

Tạo tài nguyên:

```http
POST /v1/orders HTTP/1.1
Content-Type: application/json

{ "customer_id": "cus_12", "items": [{ "product_id": "prd_7", "quantity": 2 }] }
```

```http
HTTP/1.1 201 Created
Location: /v1/orders/ord_104
Content-Type: application/json

{ "data": { "id": "ord_104", "customer_id": "cus_12", "status": "pending" } }
```

Hành động đặc biệt:

```http
POST /v1/orders/ord_104/cancel HTTP/1.1
```

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "error": {
    "code": "ORDER_ALREADY_PAID",
    "message": "A paid order cannot be cancelled.",
    "request_id": "req_c2e9d0"
  }
}
```

---

## 4. Phê duyệt

| Việc | Trạng thái |
|---|---|
| Ngôn ngữ mã lỗi/thông điệp (DEC-0001) | ⏳ Chờ xác nhận – đang dùng giả định tạm |
| Tech lead review và đồng ý áp dụng cho API mới | ⏳ Chờ review |
