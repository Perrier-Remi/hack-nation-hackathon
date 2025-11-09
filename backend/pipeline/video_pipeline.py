import inspect
import os
import analyzers
from pipeline.llm_summary import generate_analysis_summary

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
        # Step 1: Run all analyzers first
        analysis_results = []
        
        for analyzer_class in self.analyzers:
            analyzer = analyzer_class(self.video_path)
            result = analyzer.run()
            analysis_results.append({
                "analyzer": analyzer_class.__name__,
                "result": result
            })
        
        # Step 2: Generate LLM summary AFTER all analyses are complete
        # LLM summary is currently disabled
        llm_summary = {
            "summary": "LLM analysis is currently disabled",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "follow_up_prompt": ""
        }
        # try:
        #     print("Generating LLM summary from analysis results...")
        #     llm_summary = generate_analysis_summary(analysis_results)
        #     print("LLM summary generated successfully")
        # except Exception as e:
        #     print(f"Error generating LLM summary: {e}")
        #     import traceback
        #     traceback.print_exc()
        #     llm_summary = {
        #         "summary": "LLM analysis unavailable",
        #         "strengths": [],
        #         "weaknesses": [],
        #         "recommendations": []
        #     }
        
        # Step 3: Combine all results (analyzers + LLM summary)
        final_results = {
            "analyzers": analysis_results,  # All analyzer scores
            "llm_summary": llm_summary      # LLM analysis summary
        }
        
        # Remove the uploaded video file after analysis
        try:
            if os.path.exists(self.video_path):
                os.remove(self.video_path)
                print(f"Removed temporary file: {self.video_path}")
        except Exception as e:
            print(f"Error removing file {self.video_path}: {str(e)}")
            
        return final_results