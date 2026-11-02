# Chuyển tiếp sang backend/ để lệnh chạy từ gốc repo vẫn hoạt động.
.PHONY: migrate migrate-status test
migrate migrate-status test:
	$(MAKE) -C backend $@
