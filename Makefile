# Chuyển tiếp sang backend/ để lệnh chạy từ gốc repo vẫn hoạt động.
# DB mặc định vẫn là app.db Ở GỐC REPO như trước khi dời; đường dẫn tương đối được
# hiểu so với thư mục gốc (đổi thành tuyệt đối trước khi chuyển vào backend/).
# Đường dẫn tuyệt đối được tính trong recipe (không chạy python3 lúc parse Makefile),
# đọc qua biến môi trường nên đường dẫn có dấu cách/ký tự đặc biệt vẫn đúng.
DATABASE_PATH ?= app.db
export DATABASE_PATH

.PHONY: migrate migrate-status test
migrate migrate-status test:
	@command -v python3 >/dev/null 2>&1 || { echo "Lỗi: cần python3 trong PATH để chạy 'make $@'." >&2; exit 1; }
	@abs=$$(python3 -c 'import os; print(os.path.abspath(os.environ["DATABASE_PATH"]))') && \
	$(MAKE) -C backend $@ DATABASE_PATH="$$abs"
