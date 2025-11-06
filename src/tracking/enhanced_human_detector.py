"""
Enhanced Human Detection Module
Improved human detection with better accuracy and recognition capabilities
"""

import cv2
import numpy as np
import logging
import time
from threading import Lock
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class EnhancedMotionDetector:
    """Enhanced motion-based human detector with improved accuracy"""
    
    def __init__(self):
        """Initialize enhanced motion detector"""
        # Background subtraction for better motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=40,  # Lower threshold for better sensitivity
            history=500       # Longer history for better background learning
        )
        
        # Morphological operation kernels
        self.small_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        self.large_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        
        # Enhanced human detection parameters
        self.min_area = 800        # Minimum detection area
        self.max_area = 25000      # Maximum detection area
        self.min_aspect_ratio = 0.3  # Minimum height/width ratio
        self.max_aspect_ratio = 4.0  # Maximum height/width ratio
        self.min_solidity = 0.3    # Minimum solidity (filled area ratio)
        
        # Multi-frame validation
        self.detection_buffer = []
        self.buffer_size = 5
        self.confidence_threshold = 0.6
        
        # Frame initialization
        self.frame_count = 0
        self.initialization_frames = 50  # More frames for better background learning
        
        logger.info("Enhanced motion detector initialized")
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Enhanced human detection with confidence scoring
        
        Args:
            frame: Input frame
            
        Returns:
            List of detections with confidence (x, y, w, h, confidence)
        """
        try:
            self.frame_count += 1
            
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Skip during initialization
            if self.frame_count < self.initialization_frames:
                return []
            
            # Enhanced preprocessing
            fg_mask = self._preprocess_mask(fg_mask)
            
            # Find and validate contours
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Extract potential human detections
            candidate_detections = []
            for contour in contours:
                detection = self._evaluate_contour(contour, frame.shape)
                if detection is not None:
                    candidate_detections.append(detection)
            
            # Apply multi-frame validation
            validated_detections = self._validate_detections(candidate_detections)
            
            return validated_detections
            
        except Exception as e:
            logger.error(f"Enhanced motion detection error: {e}")
            return []
    
    def _preprocess_mask(self, mask: np.ndarray) -> np.ndarray:
        """Enhanced mask preprocessing"""
        # Remove noise with morphological opening
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.small_kernel)
        
        # Fill gaps with morphological closing
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.large_kernel)
        
        # Additional dilation to connect nearby regions
        mask = cv2.dilate(mask, self.small_kernel, iterations=2)
        
        return mask
    
    def _evaluate_contour(self, contour: np.ndarray, frame_shape: tuple) -> Optional[Tuple[int, int, int, int, float]]:
        """Evaluate if a contour represents a human with confidence score"""
        area = cv2.contourArea(contour)
        
        # Area filtering
        if area < self.min_area or area > self.max_area:
            return None
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        
        # Aspect ratio check
        aspect_ratio = h / w if w > 0 else 0
        if not (self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio):
            return None
        
        # Solidity check (how filled the contour is)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        if solidity < self.min_solidity:
            return None
        
        # Frame boundary check
        frame_height, frame_width = frame_shape[:2]
        if x < 0 or y < 0 or x + w > frame_width or y + h > frame_height:
            return None
        
        # Calculate confidence score based on multiple factors
        confidence = self._calculate_confidence(area, aspect_ratio, solidity, w, h, frame_shape)
        
        if confidence > self.confidence_threshold:
            return (x, y, w, h, confidence)
        
        return None
    
    def _calculate_confidence(self, area: float, aspect_ratio: float, solidity: float, 
                            w: int, h: int, frame_shape: tuple) -> float:
        """Calculate detection confidence based on human-like characteristics"""
        frame_height, frame_width = frame_shape[:2]
        
        # Initialize confidence
        confidence = 0.0
        
        # Area score (prefer medium-sized detections)
        ideal_area = 5000  # Ideal human area in pixels
        area_score = 1.0 - abs(area - ideal_area) / ideal_area
        area_score = max(0, min(1, area_score))
        confidence += area_score * 0.3
        
        # Aspect ratio score (prefer human-like proportions)
        ideal_aspect_ratio = 2.0  # Typical human height/width ratio
        aspect_score = 1.0 - abs(aspect_ratio - ideal_aspect_ratio) / ideal_aspect_ratio
        aspect_score = max(0, min(1, aspect_score))
        confidence += aspect_score * 0.4
        
        # Solidity score (humans should be reasonably filled)
        solidity_score = min(1.0, solidity / 0.7)  # Normalize to 0.7 as ideal
        confidence += solidity_score * 0.2
        
        # Size relative to frame (prefer medium-sized relative to frame)
        relative_size = (w * h) / (frame_width * frame_height)
        if 0.05 <= relative_size <= 0.3:  # 5% to 30% of frame
            size_score = 1.0
        else:
            size_score = 0.5
        confidence += size_score * 0.1
        
        return confidence
    
    def _validate_detections(self, detections: List[Tuple[int, int, int, int, float]]) -> List[Tuple[int, int, int, int, float]]:
        """Multi-frame validation for stable detections"""
        self.detection_buffer.append(detections)
        if len(self.detection_buffer) > self.buffer_size:
            self.detection_buffer.pop(0)
        
        if len(self.detection_buffer) < 3:
            return detections
        
        # Validate based on temporal consistency
        validated = []
        for current_detection in detections:
            x, y, w, h, conf = current_detection
            center_x, center_y = x + w // 2, y + h // 2
            
            # Count consistent detections in recent frames
            consistent_count = 0
            total_confidence = conf
            
            for prev_detections in self.detection_buffer[:-1]:
                for prev_det in prev_detections:
                    px, py, pw, ph, prev_conf = prev_det
                    prev_center_x, prev_center_y = px + pw // 2, py + ph // 2
                    
                    # Check spatial consistency
                    distance = np.sqrt((center_x - prev_center_x)**2 + (center_y - prev_center_y)**2)
                    if distance < 60:  # Reasonable movement threshold
                        consistent_count += 1
                        total_confidence += prev_conf
                        break
            
            # Require consistency in at least 60% of recent frames
            if consistent_count >= len(self.detection_buffer) * 0.6:
                avg_confidence = total_confidence / (consistent_count + 1)
                validated.append((x, y, w, h, avg_confidence))
        
        return validated


class EnhancedEdgeDetector:
    """Enhanced edge-based human detector with shape analysis"""
    
    def __init__(self):
        """Initialize enhanced edge detector"""
        # Multi-scale edge detection
        self.canny_low = 30
        self.canny_high = 100
        
        # Morphological kernels
        self.small_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        self.large_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        
        # Enhanced filtering parameters
        self.min_contour_area = 1000
        self.max_contour_area = 20000
        self.min_aspect_ratio = 0.4
        self.max_aspect_ratio = 3.5
        
        # Shape analysis parameters
        self.min_rectangularity = 0.4  # How rectangle-like the shape is
        self.edge_density_threshold = 0.1  # Minimum edge density
        
        logger.info("Enhanced edge detector initialized")
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Enhanced edge-based human detection
        
        Args:
            frame: Input frame
            
        Returns:
            List of detections with confidence (x, y, w, h, confidence)
        """
        try:
            # Multi-stage preprocessing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Histogram equalization for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Gaussian blur for noise reduction
            blurred = cv2.GaussianBlur(gray, (5, 5), 1.4)
            
            # Multi-scale edge detection
            edges1 = cv2.Canny(blurred, self.canny_low, self.canny_high)
            edges2 = cv2.Canny(blurred, self.canny_low // 2, self.canny_high // 2)
            
            # Combine edges
            edges = cv2.bitwise_or(edges1, edges2)
            
            # Morphological processing
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, self.large_kernel)
            edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, self.small_kernel)
            
            # Find and analyze contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            for contour in contours:
                detection = self._analyze_shape(contour, frame.shape, edges)
                if detection is not None:
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Enhanced edge detection error: {e}")
            return []
    
    def _analyze_shape(self, contour: np.ndarray, frame_shape: tuple, edge_image: np.ndarray) -> Optional[Tuple[int, int, int, int, float]]:
        """Analyze contour shape for human-like characteristics"""
        area = cv2.contourArea(contour)
        
        if area < self.min_contour_area or area > self.max_contour_area:
            return None
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(contour)
        
        # Aspect ratio check
        aspect_ratio = h / w if w > 0 else 0
        if not (self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio):
            return None
        
        # Rectangularity (how much the contour fills its bounding rectangle)
        rectangularity = area / (w * h) if w * h > 0 else 0
        if rectangularity < self.min_rectangularity:
            return None
        
        # Edge density within bounding box
        roi = edge_image[y:y+h, x:x+w]
        edge_pixels = np.count_nonzero(roi)
        edge_density = edge_pixels / (w * h) if w * h > 0 else 0
        
        if edge_density < self.edge_density_threshold:
            return None
        
        # Calculate confidence
        confidence = self._calculate_shape_confidence(area, aspect_ratio, rectangularity, edge_density)
        
        if confidence > 0.5:  # Confidence threshold
            return (x, y, w, h, confidence)
        
        return None
    
    def _calculate_shape_confidence(self, area: float, aspect_ratio: float, 
                                  rectangularity: float, edge_density: float) -> float:
        """Calculate confidence based on shape characteristics"""
        confidence = 0.0
        
        # Aspect ratio score (prefer human-like proportions)
        ideal_aspect = 2.2
        aspect_score = 1.0 - abs(aspect_ratio - ideal_aspect) / ideal_aspect
        aspect_score = max(0, min(1, aspect_score))
        confidence += aspect_score * 0.4
        
        # Rectangularity score
        rect_score = min(1.0, rectangularity / 0.6)  # Normalize to 0.6 as ideal
        confidence += rect_score * 0.3
        
        # Edge density score
        edge_score = min(1.0, edge_density / 0.2)  # Normalize to 0.2 as ideal
        confidence += edge_score * 0.2
        
        # Area score (prefer medium sizes)
        if 2000 <= area <= 10000:
            area_score = 1.0
        else:
            area_score = 0.5
        confidence += area_score * 0.1
        
        return confidence


class HybridHumanDetector:
    """Hybrid detector combining multiple detection methods for better accuracy"""
    
    def __init__(self):
        """Initialize hybrid detector"""
        self.motion_detector = EnhancedMotionDetector()
        self.edge_detector = EnhancedEdgeDetector()
        
        # Fusion parameters
        self.motion_weight = 0.6
        self.edge_weight = 0.4
        self.min_consensus_confidence = 0.5
        
        logger.info("Hybrid human detector initialized")
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Hybrid detection using multiple methods
        
        Args:
            frame: Input frame
            
        Returns:
            List of fused detections with confidence (x, y, w, h, confidence)
        """
        try:
            # Get detections from both methods
            motion_detections = self.motion_detector.detect_humans(frame)
            edge_detections = self.edge_detector.detect_humans(frame)
            
            # Fuse detections
            fused_detections = self._fuse_detections(motion_detections, edge_detections)
            
            return fused_detections
            
        except Exception as e:
            logger.error(f"Hybrid detection error: {e}")
            return []
    
    def _fuse_detections(self, motion_dets: List[Tuple[int, int, int, int, float]], 
                        edge_dets: List[Tuple[int, int, int, int, float]]) -> List[Tuple[int, int, int, int, float]]:
        """Fuse detections from multiple methods"""
        fused = []
        
        # First, add high-confidence motion detections
        for motion_det in motion_dets:
            mx, my, mw, mh, m_conf = motion_det
            m_center = (mx + mw//2, my + mh//2)
            
            # Look for corresponding edge detection
            best_edge_match = None
            best_overlap = 0
            
            for edge_det in edge_dets:
                ex, ey, ew, eh, e_conf = edge_det
                
                # Calculate overlap
                overlap = self._calculate_overlap((mx, my, mw, mh), (ex, ey, ew, eh))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_edge_match = edge_det
            
            # Fuse if good overlap found
            if best_edge_match and best_overlap > 0.3:
                ex, ey, ew, eh, e_conf = best_edge_match
                
                # Weighted fusion of coordinates
                fx = int(mx * self.motion_weight + ex * self.edge_weight)
                fy = int(my * self.motion_weight + ey * self.edge_weight)
                fw = int(mw * self.motion_weight + ew * self.edge_weight)
                fh = int(mh * self.motion_weight + eh * self.edge_weight)
                
                # Combined confidence
                f_conf = m_conf * self.motion_weight + e_conf * self.edge_weight + 0.1  # Bonus for consensus
                
                fused.append((fx, fy, fw, fh, min(1.0, f_conf)))
            else:
                # Use motion detection if confidence is high enough
                if m_conf > 0.7:
                    fused.append(motion_det)
        
        # Add edge detections that don't overlap with motion detections
        for edge_det in edge_dets:
            ex, ey, ew, eh, e_conf = edge_det
            
            # Check if this edge detection overlaps with any fused detection
            overlaps = False
            for fused_det in fused:
                fx, fy, fw, fh, _ = fused_det
                if self._calculate_overlap((ex, ey, ew, eh), (fx, fy, fw, fh)) > 0.3:
                    overlaps = True
                    break
            
            # Add if no overlap and high confidence
            if not overlaps and e_conf > 0.8:
                fused.append(edge_det)
        
        # Filter by minimum consensus confidence
        final_detections = [det for det in fused if det[4] > self.min_consensus_confidence]
        
        return final_detections
    
    def _calculate_overlap(self, box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
        """Calculate overlap ratio between two bounding boxes"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate intersection
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left < right and top < bottom:
            intersection = (right - left) * (bottom - top)
            union = w1 * h1 + w2 * h2 - intersection
            return intersection / union if union > 0 else 0
        
        return 0