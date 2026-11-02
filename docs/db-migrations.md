# Quy ước migration schema DB (REQ-008)

Phạm vi: thay đổi **schema** DB. Việc chuyển dữ liệu từ Excel nằm ngoài phạm vi tài liệu này.

## Vị trí và đặt tên

Migration nằm trong `backend/db/migrations/`, mỗi migration là một cặp file SQL:

```
backend/db/migrations/<VERSION>_<mo_ta>.up.sql     # bắt buộc: áp dụng thay đổi
backend/db/migrations/<VERSION>_<mo_ta>.down.sql   # rollback (khuyến khích; nếu thiếu thì không rollback được)
```

- `VERSION`: số thứ tự 4 chữ số, bắt đầu `0001`, tăng liên tục, **không được nhảy số**.
- `mo_ta`: `snake_case` chữ thường/số, động từ + đối tượng (`create_...`, `add_..._to_...`).
- Regex: `^\d{4}_[a-z0-9]+(_[a-z0-9]+)*\.(up|down)\.sql$`. File sai tên làm runner báo lỗi.

Ví dụ:

```
backend/db/migrations/0001_create_app_info.up.sql
backend/db/migrations/0001_create_app_info.down.sql
backend/db/migrations/0002_create_users.up.sql
backend/db/migrations/0002_create_users.down.sql
backend/db/migrations/0003_add_email_to_users.up.sql
```

## Thứ tự áp dụng

- Áp tuần tự theo `VERSION` tăng dần; chỉ áp những version chưa có trong bảng `schema_migrations`.
- Ví dụ: DB trống → `0001`, `0002`, `0003`. DB đã ở `0002` → chỉ áp `0003`.
- Mỗi migration chạy trong **một transaction** cùng việc ghi `schema_migrations`; lỗi thì rollback migration đó và dừng.
- Hai nhánh cùng tạo cùng số: người merge sau đổi lại số (đánh số lại trước khi merge).

## Quy tắc

- **Không sửa migration đã merge/áp dụng**; muốn đổi thì thêm migration mới. Runner lưu checksum SHA-256 của `.up.sql` và từ chối chạy nếu checksum đã áp dụng bị đổi.
- Mỗi lệnh SQL kết thúc bằng `;`. Một migration làm một thay đổi có ý nghĩa gắn kết.
- Khi thêm migration, cập nhật `EXPECTED_TABLES` trong `backend/tests/integration/test_migrations_empty_db.py`.

## Cách áp dụng (một lệnh)

```
make migrate                         # từ gốc: DB mặc định <gốc>/app.db (đổi: make migrate DATABASE_PATH=/path/x.db)
make -C backend migrate              # trong backend/: DB mặc định backend/app.db
python3 backend/db/migrate.py up --db PATH    # tương đương; hoặc đặt biến môi trường DATABASE_PATH
python3 backend/db/migrate.py up --db PATH --target 0002   # áp đến version 0002
python3 backend/db/migrate.py status --db PATH             # applied / pending
```

Runner chỉ dùng thư viện chuẩn Python 3 (driver SQLite). Bảng `schema_migrations(version, name, checksum, applied_at)` được tạo tự động.

## Rollback

```
python3 backend/db/migrate.py down --db PATH             # lùi 1 migration mới nhất
python3 backend/db/migrate.py down --db PATH --steps 2   # lùi 2
```

Chạy `.down.sql` theo thứ tự ngược, trong transaction, rồi xoá bản ghi trong `schema_migrations`. Thiếu `.down.sql` thì lỗi và không đổi gì. Trên production ưu tiên "roll forward" (migration mới sửa lỗi); rollback dùng chủ yếu cho dev/test.

## Kiểm thử

```
make -C backend test
```

- Unit test: `backend/tests/unit/test_migrate.py` (đặt tên, thứ tự, checksum, rollback transaction).
- Integration test: `backend/tests/integration/test_migrations_empty_db.py` áp toàn bộ migration thật lên DB test trống và so khớp schema mong đợi.
