# Chuyển tiếp sang backend/ để lệnh chạy từ gốc repo vẫn hoạt động.
# DB mặc định vẫn là app.db Ở GỐC REPO như trước khi dời; đường dẫn tương đối được
# hiểu so với thư mục gốc (đổi thành tuyệt đối trước khi chuyển vào backend/).
DATABASE_PATH ?= app.db
# Không dùng $(abspath): nó tách theo khoảng trắng nên đường dẫn có dấu cách bị sai.
ABS_DATABASE_PATH := $(shell python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$(DATABASE_PATH)")

.PHONY: migrate migrate-status test
migrate migrate-status test:
	$(MAKE) -C backend $@ DATABASE_PATH="$(ABS_DATABASE_PATH)"
