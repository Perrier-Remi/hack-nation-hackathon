.PHONY: clean-audio clean-frames clean-transcripts clean-videos clean-artifacts clean-all help list-artifacts

help:
	@echo "Available targets:"
	@echo "  clean-audio       - Remove all extracted audio files"
	@echo "  clean-frames      - Remove all extracted frame files"
	@echo "  clean-transcripts - Remove all generated transcripts"
	@echo "  clean-videos      - Remove all uploaded video files"
	@echo "  clean-artifacts   - Remove audio, frames, and transcripts (keeps videos)"
	@echo "  clean-all         - Remove everything including videos and Python cache"
	@echo "  list-artifacts    - Show disk usage of generated files"
	@echo "  help              - Show this help message"

list-artifacts:
	@echo "📊 Disk usage of generated files:"
	@echo ""
	@if [ -d "uploads/audio" ]; then \
		echo "🎵 Audio files:"; \
		du -sh uploads/audio 2>/dev/null || echo "  (empty)"; \
	fi
	@if [ -d "uploads/frames" ]; then \
		echo "🖼️  Frame files:"; \
		du -sh uploads/frames 2>/dev/null || echo "  (empty)"; \
	fi
	@if [ -d "uploads/transcripts" ]; then \
		echo "📝 Transcripts:"; \
		du -sh uploads/transcripts 2>/dev/null || echo "  (empty)"; \
	fi
	@if [ -d "uploads" ]; then \
		echo "🎬 Videos:"; \
		find uploads -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.webm" \) -exec du -ch {} + 2>/dev/null | tail -1 || echo "  (none)"; \
	fi
	@echo ""
	@echo "Total uploads directory:"; \
	du -sh uploads 2>/dev/null || echo "  (empty)"

clean-audio:
	@echo "🧹 Cleaning audio files..."
	@rm -rf uploads/audio/
	@rm -rf audio/
	@echo "✓ Audio files cleaned!"

clean-frames:
	@echo "🧹 Cleaning frame files..."
	@rm -rf uploads/frames/
	@echo "✓ Frame files cleaned!"

clean-transcripts:
	@echo "🧹 Cleaning transcripts..."
	@rm -rf uploads/transcripts/
	@rm -rf transcripts/
	@echo "✓ Transcripts cleaned!"

clean-videos:
	@echo "🧹 Cleaning uploaded videos..."
	@find uploads -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.webm" \) -delete 2>/dev/null || true
	@echo "✓ Videos cleaned!"

clean-artifacts: clean-audio clean-frames clean-transcripts
	@echo "✅ All artifacts cleaned (videos preserved)!"

clean-all: clean-artifacts clean-videos
	@echo "🧹 Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Everything cleaned!"

