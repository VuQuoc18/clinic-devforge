# Quy ước đặt mã BR/FR/REQ trong tên test (REQ-009)

Mục đích: truy vết từ yêu cầu nghiệp vụ (BR), yêu cầu chức năng (FR) và REQ tới test, bằng một lệnh tìm chuỗi.

## 1. Quy tắc

1. **Giữ nguyên dạng mã** như trong tài liệu nghiệp vụ: chữ hoa, dấu gạch ngang. Ví dụ `BR-TD-01`, `FR-TD-01`, `REQ-009`. Không đổi thành chữ thường, không đổi `-` thành `_` ở chỗ dùng để tìm kiếm.
   Định dạng cố định: `BR-<NHÓM>-<2 chữ số>` và `FR-<NHÓM>-<2 chữ số>` (NHÓM là chữ hoa A-Z, ví dụ `TD`), `REQ-<3 chữ số>`. Test `tests/unit/test_traceability_convention.py` kiểm tra định dạng này trên docstring của mọi test trong `tests/`.
2. Mã nằm ở **dòng đầu của docstring** của test, đặt trong ngoặc vuông, trước phần mô tả:

   ```
   """[BR-TD-01] mô tả ngắn hành vi được kiểm tra"""
   ```

   Với `unittest`, dòng đầu docstring hiển thị cùng tên test khi chạy `make test` (target có trong `Makefile`, chạy `python3 -m unittest discover -s tests -t . -v`).
   `pytest -v` **không** hiển thị docstring, chỉ hiển thị tên hàm; với pytest, mã thấy được qua dạng gạch dưới ở quy tắc 3 và lọc được bằng `python -m pytest tests -v -k br_td_01`.
3. Tên hàm/phương thức test (định danh Python không có dấu `-`) chứa thêm dạng gạch dưới thường của mã, ví dụ `test_br_td_01_...`, để thấy mã ngay trong tên và trong báo cáo pytest.
4. Một test có thể mang nhiều mã: `[BR-TD-01][FR-TD-01][REQ-009]`. Mỗi mã đặt trong cặp ngoặc vuông riêng, không có khoảng trắng giữa các cặp.
5. Chỉ ghi mã trong test **thực sự kiểm tra** yêu cầu đó. Không ghi mã vào file test không liên quan.
   **Ngoại lệ:** test mẫu `tests/unit/test_traceability_convention.py` mượn `BR-TD-01` và `FR-TD-01` làm mã minh họa (theo tiêu chí chấp nhận của REQ-009); hai test này chỉ kiểm tra chính quy ước, không kiểm tra quy tắc nghiệp vụ của các mã đó. Khi có test nghiệp vụ thật cho `BR-TD-01`/`FR-TD-01`, gỡ mã khỏi test mẫu (đổi sang mã giả như `BR-XX-00`). Test mẫu mang `REQ-009` là mã thật vì nó kiểm tra đúng quy ước này.
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

Kết quả mong đợi cho `BR-TD-01`: có các dòng thuộc test mẫu `tests/unit/test_traceability_convention.py`; khi có test thật gắn cùng mã (quy tắc 6), kết quả có thêm các file đó. Liệt kê chỉ tên file:

```bash
grep -rl --include="*.py" "BR-TD-01" tests
```

Tìm mọi test có gắn mã (mọi loại):

```bash
grep -rnE --include="*.py" "\[(BR|FR)-[A-Z]+-[0-9]{2}\]|\[REQ-[0-9]{3}\]" tests
```

Lệnh tìm dùng `grep` (Linux/macOS/Git Bash); không có `grep` thì test tích hợp tự bỏ qua.

Kiểm tra tự động quy ước và lệnh tìm: `python3 -m unittest tests.unit.test_traceability_convention tests.integration.test_traceability_grep`.
