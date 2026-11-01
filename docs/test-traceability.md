# Quy ước đặt mã BR/FR/REQ trong tên test (REQ-009)

Mục đích: truy vết từ yêu cầu nghiệp vụ (BR), yêu cầu chức năng (FR) và REQ tới test, bằng một lệnh tìm chuỗi.

## 1. Quy tắc

1. **Giữ nguyên dạng mã** như trong tài liệu nghiệp vụ: chữ hoa, dấu gạch ngang. Ví dụ `BR-TD-01`, `FR-TD-01`, `REQ-009`. Không đổi thành chữ thường, không đổi `-` thành `_` ở chỗ dùng để tìm kiếm.
2. Mã nằm ở **dòng đầu của docstring** của test, đặt trong ngoặc vuông, trước phần mô tả:

   ```
   """[BR-TD-01] mô tả ngắn hành vi được kiểm tra"""
   ```

   Với `unittest`, dòng đầu docstring hiển thị trong tên test khi chạy `python3 -m unittest -v` (Makefile: `make test`).
3. Tên hàm/phương thức test (định danh Python không có dấu `-`) chứa thêm dạng gạch dưới thường của mã, ví dụ `test_br_td_01_...`, để thấy mã ngay trong tên và trong báo cáo pytest.
4. Một test có thể mang nhiều mã: `[BR-TD-01][FR-TD-01][REQ-009]`. Mỗi mã đặt trong cặp ngoặc vuông riêng, không có khoảng trắng giữa các cặp.
5. Chỉ ghi mã trong test **thực sự kiểm tra** yêu cầu đó. Không ghi mã vào file test không liên quan.
6. Test mới cho một BR/FR/REQ phải mang mã tương ứng. Test cũ bổ sung dần khi sửa tới.

## 2. Ví dụ

| Loại | Mã | Dòng đầu docstring | Tên hàm |
| --- | --- | --- | --- |
| BR | `BR-TD-01` | `"""[BR-TD-01] ..."""` | `test_br_td_01_...` |
| FR | `FR-TD-01` | `"""[FR-TD-01] ..."""` | `test_fr_td_01_...` |
| REQ | `REQ-009` | `"""[REQ-009] ..."""` | `test_req_009_...` |
| Nhiều mã | `BR-TD-01`, `FR-TD-01`, `REQ-009` | `"""[BR-TD-01][FR-TD-01][REQ-009] ..."""` | `test_br_td_01_fr_td_01_...` |

Ví dụ đầy đủ:

```python
class TraceabilityTest(unittest.TestCase):
    def test_br_td_01_example(self):
        """[BR-TD-01] mô tả hành vi nghiệp vụ được kiểm tra"""
```

Test mẫu theo quy ước: `tests/unit/test_traceability_convention.py`.

## 3. Tìm test theo mã

Chạy ở gốc repo. Dùng `--include="*.py"` để bỏ qua file `.pyc` và chỉ tìm trong thư mục `tests`:

```bash
grep -rn --include="*.py" "BR-TD-01" tests
grep -rn --include="*.py" "FR-TD-01" tests
grep -rn --include="*.py" "REQ-009" tests
```

Kết quả mong đợi cho `BR-TD-01`: các dòng thuộc `tests/unit/test_traceability_convention.py`. Liệt kê chỉ tên file:

```bash
grep -rl --include="*.py" "BR-TD-01" tests
```

Tìm mọi test có gắn mã (mọi loại):

```bash
grep -rnE --include="*.py" "\[(BR|FR)-[A-Z]+-[0-9]+\]|\[REQ-[0-9]+\]" tests
```

Kiểm tra tự động quy ước và lệnh tìm: `python3 -m unittest tests.unit.test_traceability_convention tests.integration.test_traceability_grep`.
