import os
import json
from typing import Dict, List, Optional
import google.generativeai as genai
from config import GOOGLE_AI_STUDIO_API_KEY, GEMINI_MODEL

# Gemini model instance (initialized on first use)
_model_instance = None

def _get_model():
    """Initialize and return the Gemini model using Google AI Studio API"""
    global _model_instance
    
    if _model_instance is not None:
        return _model_instance
    
    if not GOOGLE_AI_STUDIO_API_KEY:
        print("⚠️  Google AI Studio API key not found in config")
        return None
    
    try:
        # Configure Gemini with API key (same as transcription_service.py)
        genai.configure(api_key=GOOGLE_AI_STUDIO_API_KEY)
        _model_instance = genai.GenerativeModel(GEMINI_MODEL)
        print(f"✓ LLM Summary initialized with model: {GEMINI_MODEL}")
        return _model_instance
    except Exception as e:
        print(f"❌ Error initializing Gemini model: {e}")
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
    # Always ensure genai is configured (fixes first-run initialization issue)
    if not GOOGLE_AI_STUDIO_API_KEY:
        return {
            "summary": "LLM analysis unavailable",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "follow_up_prompt": ""
        }
    
    genai.configure(api_key=GOOGLE_AI_STUDIO_API_KEY)
    
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
    prompt = f"""Analyze this video content quality assessment. Be concise but specific.

Technical Metrics:
{analysis_text}

Focus on visual quality metrics (resolution, sharpness, color, lighting). 
Face detection is a minor indicator only.

Provide:
1. Overall assessment (1-2 sentences)
2. Top 3 strengths (bullet points)
3. Top 3 weaknesses (bullet points)
4. Top 3 actionable recommendations (1-2 phrases each, very short)
5. Follow-up prompt for content improvement (concise technical suggestions to improve the next version based on this analysis)

Format as JSON:
{{
  "overall": "brief assessment",
  "strengths": ["strength1", "strength2", "strength3"],
  "weaknesses": ["weakness1", "weakness2", "weakness3"],
  "recommendations": ["short rec1", "short rec2", "short rec3"],
  "follow_up_prompt": "concise technical prompt for next iteration"
}}

Keep recommendations to 1-2 phrases maximum. Be direct and actionable.
The follow-up prompt should be a concise, actionable prompt that can be used to generate an improved version of this content."""
    
    try:
        # Configure safety settings to be less restrictive for business/technical content
        # Use proper HarmCategory enum values
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 2048,  # Increased to allow full response
            },
            safety_settings=safety_settings
        )
        
        # Check if response was blocked
        if not response.candidates:
            return {
                "summary": "Analysis generated with basic metrics",
                "strengths": ["Video processed successfully"],
                "weaknesses": ["Advanced analysis unavailable"],
                "recommendations": ["Review quality metrics"],
                "follow_up_prompt": ""
            }
        
        # Check if the first candidate was blocked
        candidate = response.candidates[0]
        if hasattr(candidate, 'finish_reason') and candidate.finish_reason.name == 'SAFETY':
            return {
                "summary": "Analysis generated with basic metrics",
                "strengths": ["Video processed successfully"],
                "weaknesses": ["Advanced analysis unavailable"],
                "recommendations": ["Review quality metrics"],
                "follow_up_prompt": ""
            }
        
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
        # Failed to parse JSON, use fallback
        return {
            "summary": "Analysis generated with basic metrics",
            "strengths": ["Video quality processed"],
            "weaknesses": ["Detailed analysis format error"],
            "recommendations": ["Review raw quality scores"],
            "follow_up_prompt": ""
        }
    except ValueError as e:
        # This catches the "response.text quick accessor" error - response was blocked
        # Try to get partial response or use fallback
        if 'response' in locals():
            # Check if we have any candidates with content
            try:
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        # Try to extract text from parts
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            text_parts = [part.text for part in candidate.content.parts if hasattr(part, 'text')]
                            if text_parts:
                                response_text = ''.join(text_parts).strip()
                                # Try parsing this as JSON
                                if "```json" in response_text:
                                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                                summary_data = json.loads(response_text)
                                return {
                                    "summary": summary_data.get("overall", ""),
                                    "strengths": summary_data.get("strengths", []),
                                    "weaknesses": summary_data.get("weaknesses", []),
                                    "recommendations": summary_data.get("recommendations", []),
                                    "follow_up_prompt": summary_data.get("follow_up_prompt", "")
                                }
            except:
                pass
        
        # If we couldn't extract content, return fallback
        return {
            "summary": "Analysis generated with basic metrics only",
            "strengths": ["Video quality metrics available"],
            "weaknesses": ["Detailed AI analysis unavailable"],
            "recommendations": ["Review manual quality assessment"],
            "follow_up_prompt": ""
        }
    except Exception as e:
        # Any other error, return fallback silently
        return {
            "summary": "Analysis completed with basic quality metrics",
            "strengths": ["Video processed"],
            "weaknesses": ["Advanced analysis unavailable"],
            "recommendations": ["Review quality scores"],
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

