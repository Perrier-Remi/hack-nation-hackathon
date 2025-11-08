import inspect
from analyzers.base_analyzer import BaseAnalyzer
import analyzers

class VideoPipeline:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.analyzers = self._discover_analyzers()
        
    def _discover_analyzers(self):
        """Automatically discover all analyzer classes in the analyzers folder"""
        analyzer_classes = []
        
        for name in dir(analyzers):
            obj = getattr(analyzers, name)
            if inspect.isclass(obj) and obj.__module__.startswith('analyzers'):
                analyzer_classes.append(obj)
        
        return analyzer_classes
        
    def run(self):
        results = []
        
        for analyzer_class in self.analyzers:
            analyzer = analyzer_class(self.video_path)
            result = analyzer.run()
            results.append({
                "analyzer": analyzer_class.__name__,
                "result": result
            })
        
        # Remove the uploaded video file after analysis
        import os
        try:
            if os.path.exists(self.video_path):
                os.remove(self.video_path)
                print(f"Removed temporary file: {self.video_path}")
        except Exception as e:
            print(f"Error removing file {self.video_path}: {str(e)}")
            
        return results