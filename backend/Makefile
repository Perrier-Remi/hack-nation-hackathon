.PHONY: clean-artifacts clean-all help

help:
	@echo "Available targets:"
	@echo "  clean-artifacts  - Remove all generated audio and frame artifacts"
	@echo "  clean-all        - Remove all artifacts including test files"
	@echo "  help             - Show this help message"

clean-artifacts:
	@echo "🧹 Cleaning audio and frame artifacts..."
	@rm -rf uploads/audio/*/
	@rm -rf uploads/frames/*/
	@rm -rf audio/
	@echo "✓ Artifacts cleaned!"

clean-all: clean-artifacts
	@echo "🧹 Cleaning all temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ All cleaned!"

