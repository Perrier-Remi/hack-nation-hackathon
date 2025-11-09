import cv2

class VideoProcessor:
    def __init__(self, video_path):
        """
        Initialize the video processor with the path to the video.
        """
        self.video_path = video_path

    def is_blurry(self, frame, threshold=100):
        """
        Check if a frame is blurry using Laplacian variance.
        Returns True if blurry.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        return lap.var() < threshold

    def sample_frames_every_half_second(self, video_name, blur_threshold=100, max_frames=60):
        """
        Sample frames every 0.5s. If the frame is blurry, take the previous frame.
        Returns list of saved frame filenames.
        """
        cap = cv2.VideoCapture(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * 0.5)  # frame step for 0.5s

        success, frame = cap.read()
        frame_count = 0
        saved_count = 0
        prev_frame = None
        saved_frames = []

        while success and saved_count < max_frames:
            # Check if this is a target frame
            if frame_count % frame_interval == 0:
                candidate_frame = frame

                # If frame is blurry, use previous frame if available
                if self.is_blurry(frame, blur_threshold):
                    if prev_frame is not None and not self.is_blurry(prev_frame, blur_threshold):
                        candidate_frame = prev_frame
                        print(f"Frame at {frame_count} is blurry, using previous frame.")
                    else:
                        print(f"Frame at {frame_count} is blurry and previous frame too, skipping.")
                        prev_frame = frame
                        success, frame = cap.read()
                        frame_count += 1
                        continue  # skip saving

                # Save the candidate frame
                filename = f"{video_name}-key_frame_{saved_count}.jpg"
                cv2.imwrite(filename, candidate_frame)
                print(f"Saved {filename} at frame {frame_count}")
                saved_frames.append(filename)
                saved_count += 1

            prev_frame = frame
            success, frame = cap.read()
            frame_count += 1

        cap.release()
        print(f"Total frames saved: {saved_count}")
        return saved_frames

"""
Example:
video_path = "./test.mp4
vide_name = "ugc_video"
video_processor = VideoProcessor(video_path)
key_frames = video_processor.sample_frames_every_half_second(video_name,blur_threshold=100, max_frames=60)
"""

