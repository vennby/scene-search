"""
Multimodal best take selection using open source AI
Combines video quality analysis + text understanding
"""
import cv2
import tempfile
import os
import json
from io import BytesIO
from PIL import Image
import numpy as np

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


def analyze_video_quality(video_data, clip_id):
    """
    Analyze video quality metrics:
    - Brightness consistency
    - Motion detection (camera stability)
    - Frame count / duration estimate
    Returns score 0-1
    """
    try:
        # Write video to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(video_data)
            tmp_path = tmp.name
        
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return 0.3  # Default low score if video can't be read
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Sample 5 frames to analyze
        sample_indices = [
            int(frame_count * i / 5) for i in range(1, 5) if int(frame_count * i / 5) < frame_count
        ]
        
        brightness_scores = []
        motion_scores = []
        prev_frame = None
        
        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Brightness analysis (avoid too dark or too bright)
            brightness = np.mean(gray)
            # Optimal brightness around 128
            brightness_score = 1.0 - abs(brightness - 128) / 128
            brightness_scores.append(max(0, min(1, brightness_score)))
            
            # Motion/stability analysis using optical flow
            if prev_frame is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    prev_frame, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                )
                magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2).mean()
                # Lower motion = more stable (score inverted)
                motion_score = 1.0 / (1.0 + magnitude / 100)  # Normalize
                motion_scores.append(max(0, min(1, motion_score)))
            
            prev_frame = gray
        
        cap.release()
        os.unlink(tmp_path)
        
        # Combine metrics
        brightness_avg = np.mean(brightness_scores) if brightness_scores else 0.5
        motion_avg = np.mean(motion_scores) if motion_scores else 0.5
        
        # Duration bonus: longer videos often better
        duration_bonus = 0.2 if frame_count > 300 else (0.1 if frame_count > 150 else 0)
        
        quality_score = (brightness_avg * 0.4 + motion_avg * 0.4) + (duration_bonus * 0.2)
        return max(0, min(1, quality_score))
    
    except Exception as e:
        print(f"Video quality analysis error: {e}")
        return 0.5


def analyze_metadata_quality(clip):
    """
    Analyze metadata quality:
    - Title completeness
    - Description quality
    - Tags relevance
    Returns score 0-1
    """
    score = 0.5  # Base score
    
    # Title quality
    if clip.title and len(clip.title) > 5:
        score += 0.15
    
    # Description quality
    if clip.description and len(clip.description) > 20:
        score += 0.2
    
    # Tags quality
    if clip.tags:
        tag_count = len(clip.tags.split(','))
        if tag_count >= 2:
            score += 0.15
    
    return min(1.0, score)


def analyze_with_llm(clips_data, scene_name):
    """
    Use transformer models to understand quality context
    Returns dict of {clip_id: refinement_score}
    """
    refinements = {}
    
    if not HAS_TRANSFORMERS:
        return refinements
    
    try:
        # Use zero-shot classification to assess quality descriptions
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        
        quality_labels = ["excellent quality", "good quality", "poor quality", "average quality"]
        
        for clip in clips_data:
            # Combine metadata for analysis
            text = f"{clip.get('title', '')} {clip.get('description', '')}"
            
            if len(text.strip()) > 5:
                result = classifier(text, quality_labels, multi_class=True)
                
                # Extract confidence for positive labels
                for label, score in zip(result['labels'], result['scores']):
                    if 'excellent' in label or 'good' in label:
                        refinements[str(clip['id'])] = score * 0.3  # Max 0.3 refinement
                        break
    
    except Exception as e:
        print(f"LLM analysis error: {e}")
    
    return refinements


def analyze_video_for_criteria(video_data, criteria):
    """
    Advanced video analysis that understands cinematography and director styles.
    Analyzes composition, editing pace, color grading, and visual complexity.
    
    Returns score 0-1 based on criteria match
    """
    if not criteria:
        return 0.5
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(video_data)
            tmp_path = tmp.name
        
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return 0.5
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Extract comprehensive visual features
        brightness_values = []
        saturation_values = []
        edge_densities = []
        color_variance = []
        frame_changes = []
        hue_distribution = []
        composition_scores = []
        prev_frame = None
        prev_gray = None
        
        # Sample more frames for better analysis
        frame_indices = []
        for i in range(min(10, frame_count)):  # Up to 10 frames
            frame_indices.append(int(frame_count * i / max(1, min(10, frame_count) - 1)))
        
        for frame_idx in frame_indices:
            if frame_idx >= frame_count:
                continue
                
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # 1. Brightness analysis
            brightness = np.mean(gray)
            brightness_values.append(brightness)
            
            # 2. Saturation - color intensity
            saturation = np.mean(hsv[:, :, 1])
            saturation_values.append(saturation)
            
            # 3. Edge density - visual complexity and sharpness
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.mean(edges) / 255.0
            edge_densities.append(edge_density)
            
            # 4. Color variance - color grading richness
            b, g, r = cv2.split(frame)
            color_var = np.std([np.std(b), np.std(g), np.std(r)])
            color_variance.append(color_var)
            
            # 5. Hue distribution - color palette analysis
            hue_hist = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            hue_dist = np.max(hue_hist) / np.mean(hue_hist) if np.mean(hue_hist) > 0 else 1
            hue_distribution.append(hue_dist)
            
            # 6. Frame-to-frame change detection (editing pace)
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                change_amount = np.mean(diff)
                frame_changes.append(change_amount)
            
            # 7. Composition analysis - center of mass, rule of thirds
            # Find focal areas (bright or high contrast areas)
            focal_score = analyze_composition(gray)
            composition_scores.append(focal_score)
            
            prev_frame = frame
            prev_gray = gray
        
        cap.release()
        os.unlink(tmp_path)
        
        # Calculate comprehensive metrics
        avg_brightness = np.mean(brightness_values) if brightness_values else 128
        brightness_variance = np.std(brightness_values) if brightness_values else 0
        
        avg_saturation = np.mean(saturation_values) if saturation_values else 100
        saturation_variance = np.std(saturation_values) if saturation_values else 0
        
        avg_edge_density = np.mean(edge_densities) if edge_densities else 0.3
        
        avg_color_variance = np.mean(color_variance) if color_variance else 40
        
        avg_frame_change = np.mean(frame_changes) if frame_changes else 0
        editing_pace = avg_frame_change  # Higher = faster cuts/transitions
        
        avg_hue_dist = np.mean(hue_distribution) if hue_distribution else 1
        
        avg_composition = np.mean(composition_scores) if composition_scores else 0.5
        
        # Analyze cinematographic style
        style = analyze_cinematography_style(
            avg_brightness, brightness_variance, avg_saturation, 
            avg_edge_density, avg_color_variance, editing_pace, avg_hue_dist
        )
        
        # Score based on criteria and detected style
        score = score_video_against_criteria(
            avg_brightness, brightness_variance, avg_saturation, saturation_variance,
            avg_edge_density, avg_color_variance, editing_pace, 
            avg_hue_dist, style, criteria, avg_composition
        )
        
        return score
    
    except Exception as e:
        print(f"Criteria analysis error: {e}")
        return 0.5


def analyze_composition(gray_frame):
    """
    Analyze frame composition - distribution of visual elements.
    Returns score indicating how well-composed the frame is.
    """
    try:
        h, w = gray_frame.shape
        
        # Detect corners/interest points (composition indicator)
        corners = cv2.cornerHarris(gray_frame, 2, 3, 0.04)
        corner_density = np.mean(corners)
        
        # Analyze quadrants (rule of thirds approximation)
        q1 = np.mean(gray_frame[:h//3, :w//3])
        q2 = np.mean(gray_frame[:h//3, w//3:2*w//3])
        q3 = np.mean(gray_frame[:h//3, 2*w//3:])
        q4 = np.mean(gray_frame[h//3:2*h//3, :w//3])
        q5 = np.mean(gray_frame[h//3:2*h//3, w//3:2*w//3])
        q6 = np.mean(gray_frame[h//3:2*h//3, 2*w//3:])
        q7 = np.mean(gray_frame[2*h//3:, :w//3])
        q8 = np.mean(gray_frame[2*h//3:, w//3:2*w//3])
        q9 = np.mean(gray_frame[2*h//3:, 2*w//3:])
        
        # Good composition has varied distribution (not all centered)
        quadrants = [q1, q2, q3, q4, q5, q6, q7, q8, q9]
        quad_variance = np.std(quadrants)
        
        # Combine metrics
        composition_score = (corner_density / 255.0 * 0.5 + quad_variance / 128.0 * 0.5)
        return min(1.0, composition_score)
    except:
        return 0.5


def analyze_cinematography_style(brightness, brightness_var, saturation, edge_density, 
                                  color_var, editing_pace, hue_diversity):
    """
    Identify cinematographic style based on visual characteristics.
    Returns dict with style indicators.
    """
    style = {
        'contrast_level': 'high' if brightness_var > 30 else 'medium' if brightness_var > 15 else 'low',
        'color_grade': 'vibrant' if saturation > 120 else 'muted' if saturation < 80 else 'balanced',
        'visual_complexity': 'complex' if edge_density > 0.4 else 'simple' if edge_density < 0.2 else 'moderate',
        'editing_speed': 'fast' if editing_pace > 30 else 'slow' if editing_pace < 10 else 'moderate',
        'color_palette': 'diverse' if hue_diversity > 1.5 else 'focused' if hue_diversity < 1.1 else 'balanced',
        'dynamic_range': 'high' if color_var > 50 else 'low' if color_var < 30 else 'medium',
    }
    return style


def score_video_against_criteria(brightness, brightness_var, saturation, saturation_var,
                                  edge_density, color_var, editing_pace, hue_diversity,
                                  style, criteria, composition_score):
    """
    Intelligently score video against criteria using cinematographic analysis.
    """
    criteria_lower = criteria.lower()
    base_score = 0.5
    
    # Michael Bay / Explosive Action style
    if any(x in criteria_lower for x in ['michael bay', 'explosive', 'action-packed', 'high octane']):
        # MB style: high contrast, fast editing, bright spots with dark areas, high saturation, complex visuals
        score = 0.3
        if style['contrast_level'] == 'high':
            score += 0.25
        if style['editing_speed'] == 'fast':
            score += 0.20
        if style['visual_complexity'] in ['complex', 'moderate']:
            score += 0.15
        if saturation > 100:
            score += 0.10
        return min(1.0, score)
    
    # Wes Anderson / Symmetrical style
    elif any(x in criteria_lower for x in ['wes anderson', 'symmetrical', 'centered', 'pastel', 'whimsical']):
        # WA style: balanced composition, centered subjects, muted/pastel colors, low editing pace
        score = 0.3
        if composition_score > 0.6:
            score += 0.20
        if style['color_grade'] == 'muted':
            score += 0.15
        if style['editing_speed'] == 'slow':
            score += 0.15
        if saturation > 80 and saturation < 130:  # Pastel range
            score += 0.10
        if style['contrast_level'] in ['low', 'medium']:
            score += 0.10
        return min(1.0, score)
    
    # Spielberg / Cinematic style
    elif any(x in criteria_lower for x in ['spielberg', 'cinematic', 'epic', 'adventure']):
        # Spielberg: balanced everything, good composition, clear focal points, moderate pacing
        score = 0.3
        if composition_score > 0.5:
            score += 0.25
        if style['visual_complexity'] == 'moderate':
            score += 0.15
        if style['editing_speed'] in ['moderate', 'slow']:
            score += 0.15
        if brightness > 100 and brightness < 180:
            score += 0.10
        if edge_density > 0.25:
            score += 0.10
        return min(1.0, score)
    
    # Nolan / Darkness & Complexity style
    elif any(x in criteria_lower for x in ['nolan', 'dark', 'complex', 'mystery', 'psychological']):
        # Nolan: dark lighting, high contrast, complex compositions, sophisticated editing
        score = 0.3
        if brightness < 130:
            score += 0.20
        if style['contrast_level'] == 'high':
            score += 0.20
        if style['visual_complexity'] in ['complex', 'moderate']:
            score += 0.15
        if edge_density > 0.3:
            score += 0.10
        if style['editing_speed'] in ['moderate', 'fast']:
            score += 0.05
        return min(1.0, score)
    
    # Regular criteria patterns
    elif any(x in criteria_lower for x in ['action', 'dynamic', 'fast', 'intense', 'explosive']):
        score = 0.3
        if style['editing_speed'] == 'fast':
            score += 0.25
        if editing_pace > 25:
            score += 0.20
        if style['contrast_level'] == 'high':
            score += 0.15
        if brightness_var > 20:
            score += 0.10
        return min(1.0, score)
    
    elif any(x in criteria_lower for x in ['sci-fi', 'futuristic', 'cyberpunk']):
        score = 0.3
        if style['contrast_level'] == 'high':
            score += 0.20
        if brightness < 140:
            score += 0.15
        if style['visual_complexity'] in ['complex', 'moderate']:
            score += 0.20
        if saturation > 100:
            score += 0.10
        if hue_diversity > 1.3:
            score += 0.05
        return min(1.0, score)
    
    elif any(x in criteria_lower for x in ['calm', 'peaceful', 'serene', 'slow', 'meditative']):
        score = 0.3
        if style['editing_speed'] == 'slow':
            score += 0.25
        if editing_pace < 15:
            score += 0.20
        if brightness_var < 25:
            score += 0.15
        if style['visual_complexity'] in ['simple', 'moderate']:
            score += 0.10
        return min(1.0, score)
    
    elif any(x in criteria_lower for x in ['dark', 'noir', 'moody', 'mysterious']):
        score = 0.3
        if brightness < 120:
            score += 0.25
        if style['contrast_level'] == 'high':
            score += 0.20
        if style['color_grade'] == 'muted':
            score += 0.15
        if saturation < 100:
            score += 0.10
        return min(1.0, score)
    
    elif any(x in criteria_lower for x in ['bright', 'vibrant', 'colorful', 'energetic']):
        score = 0.3
        if brightness > 150:
            score += 0.20
        if saturation > 120:
            score += 0.25
        if style['color_grade'] == 'vibrant':
            score += 0.15
        if hue_diversity > 1.4:
            score += 0.10
        return min(1.0, score)
    
    elif any(x in criteria_lower for x in ['soft', 'gentle', 'romantic', 'dreamy']):
        score = 0.3
        if brightness > 140:
            score += 0.15
        if saturation_var < 20:
            score += 0.15
        if style['contrast_level'] in ['low', 'medium']:
            score += 0.20
        if saturation < 110:
            score += 0.10
        if edge_density < 0.3:
            score += 0.10
        return min(1.0, score)
    
    elif any(x in criteria_lower for x in ['technical', 'detailed', 'precise', 'sharp']):
        score = 0.3
        if edge_density > 0.35:
            score += 0.30
        if style['visual_complexity'] in ['complex', 'moderate']:
            score += 0.20
        if brightness > 110:
            score += 0.10
        if saturation > 90:
            score += 0.10
        return min(1.0, score)
    
    # Default scoring
    else:
        score = 0.5
        # Slight preference for balanced characteristics
        if 100 < brightness < 160:
            score += 0.10
        if style['editing_speed'] == 'moderate':
            score += 0.10
        if style['contrast_level'] == 'medium':
            score += 0.10
        return min(1.0, score)


def analyze_takes(takes_obj, clips, criteria=None):
    """
    Multimodal analysis combining:
    1. Video quality metrics (brightness, motion, stability)
    2. Metadata quality (title, description, tags)
    3. LLM-based understanding (using transformers)
    4. Criteria-based matching (if criteria provided)
    
    Args:
        takes_obj: Takes object
        clips: List of VideoClip objects
        criteria: Optional string describing what to look for (e.g., "surprised tone")
    
    Returns tuple: (scores_dict, reasoning_dict) where:
        scores_dict = {clip_id: score 0-1}
        reasoning_dict = {clip_id: "explanation string"}
    """
    scores = {}
    reasoning = {}
    clips_data = []
    
    # Phase 1: Video quality analysis
    video_scores = {}
    for clip in clips:
        try:
            video_score = analyze_video_quality(clip.video_data, clip.id)
            video_scores[str(clip.id)] = video_score
        except Exception as e:
            print(f"Video analysis failed for clip {clip.id}: {e}")
            video_scores[str(clip.id)] = 0.5
        
        clips_data.append({
            'id': clip.id,
            'title': clip.title,
            'description': clip.description,
            'tags': clip.tags
        })
    
    # Phase 2: Metadata quality analysis
    metadata_scores = {}
    for clip in clips:
        metadata_scores[str(clip.id)] = analyze_metadata_quality(clip)
    
    # Phase 3: Criteria-based analysis (if provided)
    criteria_scores = {}
    if criteria:
        for clip in clips:
            try:
                criteria_score = analyze_video_for_criteria(clip.video_data, criteria)
                criteria_scores[str(clip.id)] = criteria_score
            except Exception as e:
                print(f"Criteria analysis failed for clip {clip.id}: {e}")
                criteria_scores[str(clip.id)] = 0.5
    
    # Phase 4: LLM refinement
    llm_refinements = analyze_with_llm(clips_data, takes_obj.scene_name)
    
    # Phase 5: Combine all scores and generate reasoning
    for clip in clips:
        clip_id_str = str(clip.id)
        
        if criteria:
            # Weighted combination with criteria emphasis
            video_component = video_scores.get(clip_id_str, 0.5) * 0.25
            metadata_component = metadata_scores.get(clip_id_str, 0.5) * 0.15
            criteria_component = criteria_scores.get(clip_id_str, 0.5) * 0.55
            llm_component = llm_refinements.get(clip_id_str, 0.1) * 0.05
        else:
            # Original weights without criteria
            video_component = video_scores.get(clip_id_str, 0.5) * 0.5
            metadata_component = metadata_scores.get(clip_id_str, 0.5) * 0.35
            criteria_component = 0
            llm_component = llm_refinements.get(clip_id_str, 0.1) * 0.15
        
        final_score = video_component + metadata_component + criteria_component + llm_component
        scores[clip_id_str] = max(0, min(1, final_score))
        
        # Generate reasoning
        reason_parts = []
        
        if criteria:
            criteria_pct = int(criteria_scores.get(clip_id_str, 0.5) * 100)
            reason_parts.append(f"Matches '{criteria}' ({criteria_pct}%)")
        
        video_pct = int(video_scores.get(clip_id_str, 0.5) * 100)
        if video_pct >= 70:
            reason_parts.append(f"Excellent video quality ({video_pct}%)")
        elif video_pct >= 50:
            reason_parts.append(f"Good video quality ({video_pct}%)")
        else:
            reason_parts.append(f"Video quality needs improvement ({video_pct}%)")
        
        metadata_pct = int(metadata_scores.get(clip_id_str, 0.5) * 100)
        if clip.title and len(clip.title) > 5:
            reason_parts.append("Complete title")
        if clip.description and len(clip.description) > 20:
            reason_parts.append("Detailed description")
        if clip.tags and len(clip.tags.split(',')) >= 2:
            reason_parts.append("Well-tagged")
        
        reasoning[clip_id_str] = " • ".join(reason_parts) if reason_parts else "Standard take"
    
    return scores, reasoning


def get_best_take_id(scores_dict, reasoning_dict, clips):
    """
    Get the clip ID with highest score and its reasoning
    """
    if not scores_dict:
        return None, None
    
    best_id = max(scores_dict, key=scores_dict.get)
    best_id_int = int(best_id) if best_id else None
    best_reason = reasoning_dict.get(best_id, "High overall quality") if best_id else None
    
    return best_id_int, best_reason
