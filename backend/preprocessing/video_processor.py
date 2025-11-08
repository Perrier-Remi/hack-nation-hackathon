import cv2

class VideoProcessor:
    def __init__(self, videoPath):
        """
        Initialize the video processor with the path to the video.
        """
        self.videoPath = videoPath

    def is_blurry(self, frame, threshold=100):
        """
        Returns True if the frame is blurry.
        Uses the variance of the Laplacian method.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        variance = lap.var()
        return variance < threshold

    def videoSampling(self, blur_threshold=100):
        """
        Detects scene changes in the video and returns timestamps (in ms)
        of key frames that are not blurry.
        """
        cap = cv2.VideoCapture(self.videoPath)
        success, prev_frame = cap.read()
        if not success:
            print("Cannot read video")
            return []

        # Get video FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Compute histogram of first frame
        prev_hist = cv2.calcHist([cv2.cvtColor(prev_frame, cv2.COLOR_BGR2HSV)], 
                                 [0], None, [256], [0,256])
        
        key_moments = []  # List to store timestamps of valid key frames

        while True:
            success, frame = cap.read()
            if not success:
                break

            # Compute histogram of current frame
            hist = cv2.calcHist([cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)], 
                                [0], None, [256], [0,256])

            # Compare with previous frame histogram
            diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)

            # If scene change detected
            if diff < 0.7:
                # Only keep frame if it is not blurry
                if not self.is_blurry(frame, blur_threshold):
                    key_moments.append(cap.get(cv2.CAP_PROP_POS_MSEC))
                    prev_hist = hist  # update histogram for next comparison
                else:
                    print(f"Blurry frame ignored at {cap.get(cv2.CAP_PROP_POS_MSEC)} ms")

        cap.release()
        return key_moments

    def save_frames(self, key_moments):
        """
        Saves frames at the given timestamps (ms) to disk.
        """
        cap = cv2.VideoCapture(self.videoPath)
        for i, t in enumerate(key_moments):
            cap.set(cv2.CAP_PROP_POS_MSEC, t)
            success, frame = cap.read()
            if success:
                filename = f"key_frame_{i}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Saved frame: {filename} at {t} ms")
            else:
                print(f"Cannot read frame at {t} ms")
        cap.release()

