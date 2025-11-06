"""
超轻量化人体检测与追踪模块
针对树莓派优化的轻量级人体检测方案
"""

import cv2
import numpy as np
import logging
import time
from threading import Lock
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class BackgroundSubtractionDetector:
    """使用背景减法的超轻量级人体检测器"""
    
    def __init__(self):
        """初始化背景减法检测器"""
        # 使用MOG2背景减法器 - 非常轻量级
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=50,  # 降低敏感度减少噪声
            history=300       # 适度的历史长度
        )
        
        # 形态学操作核
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
        # 检测参数
        self.min_contour_area = 800     # 最小轮廓面积
        self.max_contour_area = 15000   # 最大轮廓面积
        self.min_aspect_ratio = 0.3     # 最小宽高比
        self.max_aspect_ratio = 2.5     # 最大宽高比
        
        # 跟踪稳定性
        self.detection_buffer = []
        self.buffer_size = 3
        
        # 初始化帧计数
        self.frame_count = 0
        self.initialization_frames = 30  # 背景学习帧数
        
        logger.info("背景减法检测器初始化完成")
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        使用背景减法检测运动目标
        
        Args:
            frame: 输入帧
            
        Returns:
            检测到的边界框列表 (x, y, w, h)
        """
        try:
            self.frame_count += 1
            
            # 背景减法
            fg_mask = self.bg_subtractor.apply(frame)
            
            # 如果还在初始化阶段，返回空结果
            if self.frame_count < self.initialization_frames:
                return []
            
            # 形态学操作去除噪声
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, self.kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            detections = []
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # 面积筛选
                if self.min_contour_area <= area <= self.max_contour_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 宽高比筛选
                    aspect_ratio = w / h if h > 0 else 0
                    if self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio:
                        detections.append((x, y, w, h))
            
            # 应用时间稳定性滤波
            self.detection_buffer.append(detections)
            if len(self.detection_buffer) > self.buffer_size:
                self.detection_buffer.pop(0)
            
            return self._stabilize_detections()
            
        except Exception as e:
            logger.error(f"背景减法检测错误: {e}")
            return []
    
    def _stabilize_detections(self) -> List[Tuple[int, int, int, int]]:
        """时间稳定性滤波"""
        if len(self.detection_buffer) < 2:
            return self.detection_buffer[-1] if self.detection_buffer else []
        
        stable_detections = []
        current_detections = self.detection_buffer[-1]
        
        for detection in current_detections:
            x, y, w, h = detection
            center_x, center_y = x + w // 2, y + h // 2
            
            # 检查是否与历史检测一致
            is_stable = False
            for prev_detections in self.detection_buffer[:-1]:
                for prev_detection in prev_detections:
                    px, py, pw, ph = prev_detection
                    prev_center_x, prev_center_y = px + pw // 2, py + ph // 2
                    
                    distance = np.sqrt((center_x - prev_center_x)**2 + (center_y - prev_center_y)**2)
                    if distance < 50:  # 像素距离阈值
                        is_stable = True
                        break
                if is_stable:
                    break
            
            if is_stable:
                stable_detections.append(detection)
        
        return stable_detections


class OpticalFlowDetector:
    """使用光流的轻量级人体检测器"""
    
    def __init__(self):
        """初始化光流检测器"""
        # Lucas-Kanade光流参数
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        
        # 特征检测参数
        self.feature_params = dict(
            maxCorners=100,
            qualityLevel=0.3,
            minDistance=7.0,
            blockSize=7
        )
        
        self.prev_gray = None
        self.tracks = []
        self.track_len = 10
        self.frame_idx = 0
        
        logger.info("光流检测器初始化完成")
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        使用光流检测运动目标
        
        Args:
            frame: 输入帧
            
        Returns:
            检测到的边界框列表 (x, y, w, h)
        """
        try:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if self.prev_gray is None:
                self.prev_gray = frame_gray
                return []
            
            # 计算光流
            if self.tracks:
                img0, img1 = self.prev_gray, frame_gray
                p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)
                p1, _st, _err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **self.lk_params)
                
                # 筛选好的跟踪点
                good_new = p1[_st == 1]
                good_old = p0[_st == 1]
                
                # 更新轨迹
                new_tracks = []
                for tr, (x, y) in zip(self.tracks, good_new.reshape(-1, 2)):
                    tr.append((x, y))
                    if len(tr) > self.track_len:
                        del tr[0]
                    new_tracks.append(tr)
                self.tracks = new_tracks
            
            # 添加新的特征点
            if self.frame_idx % 5 == 0:  # 每5帧检测新特征
                mask = np.zeros_like(frame_gray)
                mask[:] = 255
                
                # 在现有轨迹周围设置掩码
                for tr in self.tracks:
                    if tr:
                        x, y = int(tr[-1][0]), int(tr[-1][1])
                        cv2.circle(mask, (x, y), 5, 0, -1)
                
                p = cv2.goodFeaturesToTrack(
                    frame_gray, 
                    maxCorners=int(self.feature_params['maxCorners']),
                    qualityLevel=self.feature_params['qualityLevel'],
                    minDistance=self.feature_params['minDistance'],
                    mask=mask,
                    blockSize=int(self.feature_params['blockSize'])
                )
                if p is not None:
                    for x, y in np.float32(p).reshape(-1, 2):
                        self.tracks.append([(x, y)])
            
            self.frame_idx += 1
            self.prev_gray = frame_gray.copy()
            
            # 基于运动轨迹生成检测框
            detections = self._generate_detections_from_tracks()
            return detections
            
        except Exception as e:
            logger.error(f"光流检测错误: {e}")
            return []
    
    def _generate_detections_from_tracks(self) -> List[Tuple[int, int, int, int]]:
        """从运动轨迹生成检测框"""
        if not self.tracks:
            return []
        
        # 聚类相近的轨迹点
        active_points = []
        for tr in self.tracks:
            if len(tr) > 3:  # 只考虑稳定的轨迹
                active_points.append(tr[-1])
        
        if not active_points:
            return []
        
        # 简单聚类
        detections = []
        points = np.array(active_points)
        
        # 使用DBSCAN或简单的距离聚类
        clusters = self._simple_clustering(points, threshold=50)
        
        for cluster in clusters:
            if len(cluster) > 3:  # 至少4个点才形成检测
                xs, ys = zip(*cluster)
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                
                # 扩展边界框
                padding = 20
                x = max(0, x_min - padding)
                y = max(0, y_min - padding)
                w = x_max - x_min + 2 * padding
                h = y_max - y_min + 2 * padding
                
                # 验证尺寸合理性
                if 30 < w < 200 and 50 < h < 300:
                    detections.append((int(x), int(y), int(w), int(h)))
        
        return detections
    
    def _simple_clustering(self, points, threshold=50):
        """简单的距离聚类"""
        if len(points) == 0:
            return []
        
        clusters = []
        used = [False] * len(points)
        
        for i, point in enumerate(points):
            if used[i]:
                continue
                
            cluster = [point]
            used[i] = True
            
            for j, other_point in enumerate(points):
                if used[j]:
                    continue
                    
                distance = np.sqrt((point[0] - other_point[0])**2 + (point[1] - other_point[1])**2)
                if distance < threshold:
                    cluster.append(other_point)
                    used[j] = True
            
            clusters.append(cluster)
        
        return clusters


class FastCascadeDetector:
    """使用Haar级联分类器的快速检测器"""
    
    def __init__(self):
        """初始化Haar级联检测器"""
        try:
            # 使用简单的人脸检测器作为后备方案
            # 在实际部署时，可以下载专门的全身检测器文件
            try:
                # 尝试使用可能存在的级联文件
                self.body_cascade = cv2.CascadeClassifier('haarcascade_fullbody.xml')
                if self.body_cascade.empty():
                    # 如果找不到全身检测器，使用人脸检测器
                    import cv2
                    face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    self.body_cascade = cv2.CascadeClassifier(face_cascade_path)
            except AttributeError:
                # 如果cv2.data不可用，创建一个虚拟检测器
                logger.warning("Haar级联检测器不可用，将使用简化检测")
                self.body_cascade = None
            
            # 检测参数
            self.scale_factor = 1.1
            self.min_neighbors = 3
            self.min_size = (30, 30)
            self.max_size = (300, 300)
            
            # 检测历史
            self.detection_buffer = []
            self.buffer_size = 3
            
            logger.info("Haar级联检测器初始化完成")
            
        except Exception as e:
            logger.error(f"Haar级联检测器初始化失败: {e}")
            raise
    
    def detect_humans(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        使用Haar级联检测人体
        
        Args:
            frame: 输入帧
            
        Returns:
            检测到的边界框列表 (x, y, w, h)
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 直方图均衡化提高对比度
            gray = cv2.equalizeHist(gray)
            
            # 检测
            detections = self.body_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=self.min_size,
                maxSize=self.max_size,
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # 转换格式
            detection_list = [(x, y, w, h) for x, y, w, h in detections]
            
            # 应用时间稳定性滤波
            self.detection_buffer.append(detection_list)
            if len(self.detection_buffer) > self.buffer_size:
                self.detection_buffer.pop(0)
            
            return self._stabilize_detections()
            
        except Exception as e:
            logger.error(f"Haar级联检测错误: {e}")
            return []
    
    def _stabilize_detections(self) -> List[Tuple[int, int, int, int]]:
        """时间稳定性滤波"""
        if len(self.detection_buffer) < 2:
            return self.detection_buffer[-1] if self.detection_buffer else []
        
        stable_detections = []
        current_detections = self.detection_buffer[-1]
        
        for detection in current_detections:
            x, y, w, h = detection
            center_x, center_y = x + w // 2, y + h // 2
            
            # 检查是否与历史检测一致
            is_stable = False
            for prev_detections in self.detection_buffer[:-1]:
                for prev_detection in prev_detections:
                    px, py, pw, ph = prev_detection
                    prev_center_x, prev_center_y = px + pw // 2, py + ph // 2
                    
                    distance = np.sqrt((center_x - prev_center_x)**2 + (center_y - prev_center_y)**2)
                    if distance < 60:
                        is_stable = True
                        break
                if is_stable:
                    break
            
            if is_stable:
                stable_detections.append(detection)
        
        return stable_detections


class LightweightHumanTracker:
    """超轻量级人体追踪器主类"""
    
    def __init__(self, camera_manager, motor_controller, detector_type='background'):
        """
        初始化轻量级人体追踪器
        
        Args:
            camera_manager: 摄像头管理器
            motor_controller: 电机控制器
            detector_type: 检测器类型 ('background', 'optical_flow', 'cascade')
        """
        self.camera_manager = camera_manager
        self.motor_controller = motor_controller
        
        # 选择检测器
        if detector_type == 'background':
            self.detector = BackgroundSubtractionDetector()
            self.detector_name = "背景减法"
        elif detector_type == 'optical_flow':
            self.detector = OpticalFlowDetector()
            self.detector_name = "光流"
        elif detector_type == 'cascade':
            self.detector = FastCascadeDetector()
            self.detector_name = "Haar级联"
        else:
            # 默认使用背景减法
            self.detector = BackgroundSubtractionDetector()
            self.detector_name = "背景减法"
        
        # 跟踪状态
        self.tracking = False
        self.lock = Lock()
        self.last_human_center = None
        
        # 简化的PID控制器
        self.pid_x = SimplePIDController(kp=0.3, ki=0.05, kd=0.1)
        self.pid_distance = SimplePIDController(kp=0.2, ki=0.02, kd=0.05)
        
        # 帧参数
        self.frame_width = 640
        self.frame_height = 480
        self.target_x = self.frame_width // 2
        self.target_distance = 120  # 目标人体高度
        
        # 控制参数
        self.max_turn_speed = 40
        self.max_forward_speed = 30
        
        # 检测失败处理
        self.frames_since_detection = 0
        self.max_frames_without_detection = 10
        
        logger.info(f"轻量级人体追踪器初始化完成，使用{self.detector_name}检测器")
    
    def start_tracking(self):
        """开始人体追踪"""
        logger.info(f"开始{self.detector_name}人体追踪...")
        self.tracking = True
        
        # 重置控制器
        self.pid_x.reset()
        self.pid_distance.reset()
        self.frames_since_detection = 0
        
        while self.tracking:
            try:
                # 获取当前帧
                frame = self.camera_manager.get_frame()
                if frame is None:
                    continue
                
                # 更新帧尺寸
                self.frame_height, self.frame_width = frame.shape[:2]
                self.target_x = self.frame_width // 2
                
                # 检测人体
                start_time = time.time()
                human_detections = self.detector.detect_humans(frame)
                detection_time = (time.time() - start_time) * 1000
                
                if human_detections:
                    # 选择最大的检测框
                    best_detection = max(human_detections, key=lambda box: box[2] * box[3])
                    x, y, w, h = best_detection
                    
                    # 计算中心点
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # 更新跟踪状态
                    with self.lock:
                        self.last_human_center = (center_x, center_y, h)
                    
                    # 控制车辆移动
                    self._track_human(center_x, h)
                    
                    # 可视化
                    self._draw_visualization(frame, x, y, w, h, center_x, center_y, detection_time)
                    
                    self.frames_since_detection = 0
                else:
                    # 未检测到人体
                    self._handle_no_detection()
                    with self.lock:
                        self.last_human_center = None
                    
                    # 状态显示
                    cv2.putText(frame, f"{self.detector_name} 搜索中... {detection_time:.1f}ms", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # 更新摄像头处理后的帧
                self.camera_manager.set_processed_frame(frame)
                
            except Exception as e:
                logger.error(f"轻量级追踪循环错误: {e}")
    
    def _track_human(self, center_x: int, human_height: int):
        """控制车辆追踪人体"""
        try:
            # 计算误差
            x_error = center_x - self.target_x
            distance_error = self.target_distance - human_height
            
            # PID控制
            turn_output = self.pid_x.update(x_error)
            speed_output = self.pid_distance.update(distance_error)
            
            # 限制输出
            turn_speed = max(-self.max_turn_speed, min(self.max_turn_speed, turn_output))
            forward_speed = max(-self.max_forward_speed, min(self.max_forward_speed, speed_output))
            
            # 死区处理
            if abs(x_error) < 30:
                turn_speed = 0
            if abs(distance_error) < 20:
                forward_speed = 0
            
            # 发送控制命令
            self.motor_controller.move_with_turn(forward_speed, turn_speed)
            
        except Exception as e:
            logger.error(f"人体追踪控制错误: {e}")
    
    def _handle_no_detection(self):
        """处理未检测到人体的情况"""
        self.frames_since_detection += 1
        
        if self.frames_since_detection < 5:
            # 短暂停止
            self.motor_controller.stop()
        elif self.frames_since_detection < self.max_frames_without_detection:
            # 轻微搜索
            self.motor_controller.move_with_turn(0, 15)
        else:
            # 完全停止
            self.motor_controller.stop()
    
    def _draw_visualization(self, frame, x, y, w, h, center_x, center_y, detection_time):
        """绘制可视化信息"""
        # 边界框
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # 中心点
        cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
        
        # 目标线
        cv2.line(frame, (self.target_x, 0), (self.target_x, self.frame_height), (255, 0, 0), 2)
        
        # 状态信息
        x_error = center_x - self.target_x
        distance_error = self.target_distance - h
        
        cv2.putText(frame, f"{self.detector_name} 追踪: X={x_error:+.0f} D={distance_error:+.0f}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"检测时间: {detection_time:.1f}ms", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def stop_tracking(self):
        """停止人体追踪"""
        logger.info("停止轻量级人体追踪...")
        self.tracking = False
        self.motor_controller.stop()
    
    def get_tracking_status(self) -> dict:
        """获取当前追踪状态"""
        with self.lock:
            return {
                'tracking': self.tracking,
                'detector_type': self.detector_name,
                'last_human_center': self.last_human_center,
                'target_center': (self.target_x, self.frame_height // 2),
                'frame_size': (self.frame_width, self.frame_height)
            }


class SimplePIDController:
    """简化的PID控制器"""
    
    def __init__(self, kp: float, ki: float, kd: float):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.previous_error = 0
        self.integral = 0
        
    def update(self, error: float) -> float:
        # P项
        p_term = self.kp * error
        
        # I项（防止积分饱和）
        self.integral += error
        self.integral = max(-50, min(50, self.integral))
        i_term = self.ki * self.integral
        
        # D项
        derivative = error - self.previous_error
        d_term = self.kd * derivative
        
        self.previous_error = error
        
        return p_term + i_term + d_term
    
    def reset(self):
        self.previous_error = 0
        self.integral = 0