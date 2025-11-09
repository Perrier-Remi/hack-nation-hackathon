import os
import json
from typing import Dict, List
from google.oauth2 import service_account
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel

# Configuration
CREDENTIALS_PATH = "gen-lang-client-0248100080-469fc2910711.json"
PROJECT_ID = "gen-lang-client-0248100080"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash"

def _get_model():
    """Initialize and return the Gemini model"""
    if not os.path.exists(CREDENTIALS_PATH):
        return None
    
    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            credentials_info = json.load(f)
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info
        )
        
        aiplatform.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        return GenerativeModel(MODEL_NAME)
    except Exception as e:
        print(f"Error initializing model: {e}")
        return None

def generate_analysis_summary(analysis_results: List[Dict]) -> Dict:
    """
    Generate a detailed but concise LLM analysis summary from analyzer results.
    
    Args:
        analysis_results: List of analyzer results with format:
            [{"analyzer": "AnalyzerName", "result": {...}}, ...]
    
    Returns:
        Dict with summary, strengths, weaknesses, and recommendations
    """
    model = _get_model()
    if model is None:
        return {
            "summary": "LLM analysis unavailable",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "follow_up_prompt": ""
        }
    
    # Format analysis results for prompt
    analysis_text = _format_analysis_results(analysis_results)
    
    # Create concise but detailed prompt
    prompt = f"""Analyze this AI-generated video ad quality assessment. Be concise but specific.

Analysis Results:
{analysis_text}

Focus primarily on visual quality metrics (resolution, sharpness, color, lighting). 
AI Face Detection is a minor indicator only - do not emphasize it heavily.

Provide:
1. Overall assessment (1-2 sentences)
2. Top 3 strengths (bullet points)
3. Top 3 weaknesses (bullet points)
4. Top 3 actionable recommendations (1-2 phrases each, very short)
5. Follow-up prompt for next ad generation (concise prompt to improve the next AI-generated ad based on this analysis)

Format as JSON:
{{
  "overall": "brief assessment",
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"],
  "recommendations": ["short rec1", "short rec2", "short rec3"],
  "follow_up_prompt": "concise prompt for next AI ad generation"
}}

Keep recommendations to 1-2 phrases maximum. Be direct and actionable.
The follow-up prompt should be a concise, actionable prompt that can be used to generate an improved version of this ad."""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 600,  # Increased for follow-up prompt
            }
        )
        
        # Parse JSON response
        response_text = response.text.strip()
        
        # Extract JSON if wrapped in markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        summary_data = json.loads(response_text)
        
        return {
            "summary": summary_data.get("overall", ""),
            "strengths": summary_data.get("strengths", []),
            "weaknesses": summary_data.get("weaknesses", []),
            "recommendations": summary_data.get("recommendations", []),
            "follow_up_prompt": summary_data.get("follow_up_prompt", "")
        }
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Response text: {response_text}")
        # Fallback: return raw response
        return {
            "summary": response.text if 'response' in locals() else "Analysis failed",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "follow_up_prompt": ""
        }
    except Exception as e:
        print(f"Error generating summary: {e}")
        return {
            "summary": f"Error: {str(e)}",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "follow_up_prompt": ""
        }

def _format_analysis_results(analysis_results: List[Dict]) -> str:
    """Format analysis results into a concise text format"""
    formatted = []
    
    for item in analysis_results:
        analyzer_name = item.get("analyzer", "Unknown")
        result = item.get("result", {})
        
        # Format based on analyzer type
        if analyzer_name == "VideoQualityAnalyzer":
            formatted.append(f"Visual Quality:")
            formatted.append(f"  Resolution: {result.get('resolution_score', 0):.2f}")
            formatted.append(f"  Sharpness: {result.get('sharpness_score', 0):.2f}")
            formatted.append(f"  Color: {result.get('color_score', 0):.2f}")
            formatted.append(f"  Lighting: {result.get('lighting_score', 0):.2f}")
            formatted.append(f"  Overall: {result.get('overall_quality', 0):.2f}")
        
        elif analyzer_name == "IAFaceDetector":
            ai_ratio = result if isinstance(result, (int, float)) else result.get('ai_face_ratio', 0)
            formatted.append(f"AI Face Detection:")
            formatted.append(f"  AI-generated faces ratio: {ai_ratio:.2f}")
            formatted.append(f"  Note that a score of 1.0 means that the video is 100% AI-generated. But this model is highly sensitive. So it may be wrong. ")
        
        elif analyzer_name == "RAPIQUEAnalyzer":
            rapique_score = result.get('rapique_score', 0) if isinstance(result, dict) else 0
            rapique_available = result.get('rapique_available', False) if isinstance(result, dict) else False
            formatted.append(f"RAPIQUE Quality Assessment:")
            if rapique_available:
                formatted.append(f"  RAPIQUE Score: {rapique_score:.2f}")
                formatted.append(f"  Method: {result.get('method', 'unknown')}")
            else:
                formatted.append(f"  Status: Not available (MATLAB or RAPIQUE repository not found)")
                if isinstance(result, dict) and 'error' in result:
                    formatted.append(f"  Error: {result['error']}")
        
        else:
            # Generic formatting
            formatted.append(f"{analyzer_name}:")
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        formatted.append(f"  {key}: {value:.2f}")
                    else:
                        formatted.append(f"  {key}: {value}")
            else:
                formatted.append(f"  Result: {result}")
        
        formatted.append("")  # Empty line between analyzers
    
    return "\n".join(formatted)

