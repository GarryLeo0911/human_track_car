# 小车视频流集成到SOFT3888项目指南

## 概述
本指南展示如何将人体跟踪小车的视频输出作为SOFT3888_F16_02_P15项目的视频输入。

## 前提条件
- 小车和电脑在同一网络下（有线连接）
- 小车系统已启动（运行 `python main.py`）
- SOFT3888项目可以正常运行

## 修改步骤

### 1. 小车端修改（已完成）
- 添加了 flask-cors 到 requirements.txt
- 在 app.py 中启用了 CORS 支持
- 视频流接口：`http://小车IP:5000/video_feed`

### 2. SOFT3888项目修改

#### 方法A: 直接替换getUserMedia（推荐）

在 `static/js/assessment.js` 中找到以下代码：
```javascript
// 现有的摄像头获取代码（约第35-50行）
stream = await navigator.mediaDevices.getUserMedia(constraints);
video = document.getElementById("video");
video.srcObject = stream;
```

替换为：
```javascript
// 使用小车视频流替代本地摄像头
const CAR_VIDEO_URL = 'http://192.168.1.100:5000/video_feed'; // 替换为实际小车IP

// 创建video元素来接收小车视频流
video = document.getElementById("video");
video.crossOrigin = 'anonymous';
video.src = CAR_VIDEO_URL;

// 创建MediaStream用于录制功能
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
canvas.width = 640;
canvas.height = 480;

// 将视频绘制到canvas并转换为stream
const drawFrame = () => {
    if (video.videoWidth > 0) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        requestAnimationFrame(drawFrame);
    }
};

video.addEventListener('loadedmetadata', () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    drawFrame();
});

// 创建用于录制的MediaStream
stream = canvas.captureStream(30); // 30 FPS
```

#### 方法B: 创建自定义视频源类

创建新文件 `static/js/car_video_source.js`：
```javascript
/**
 * Car Video Source Integration
 * 将小车视频流作为SOFT3888项目的视频输入源
 */
export class CarVideoSource {
    constructor(carIp = '192.168.1.100', carPort = 5000) {
        this.carVideoUrl = `http://${carIp}:${carPort}/video_feed`;
        this.video = null;
        this.canvas = null;
        this.stream = null;
        this.isInitialized = false;
    }

    /**
     * 初始化小车视频源
     * @returns {Promise<MediaStream>} 返回MediaStream用于后续处理
     */
    async initialize() {
        try {
            // 创建video元素
            this.video = document.createElement('video');
            this.video.crossOrigin = 'anonymous';
            this.video.autoplay = true;
            this.video.muted = true;
            this.video.playsInline = true;
            this.video.src = this.carVideoUrl;

            // 等待视频加载
            await new Promise((resolve, reject) => {
                this.video.addEventListener('loadedmetadata', resolve);
                this.video.addEventListener('error', reject);
                setTimeout(() => reject(new Error('Video load timeout')), 10000);
            });

            // 创建canvas用于转换
            this.canvas = document.createElement('canvas');
            this.canvas.width = this.video.videoWidth || 640;
            this.canvas.height = this.video.videoHeight || 480;
            const ctx = this.canvas.getContext('2d');

            // 持续绘制视频帧到canvas
            const drawLoop = () => {
                if (this.video && !this.video.paused && !this.video.ended) {
                    ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
                }
                requestAnimationFrame(drawLoop);
            };
            drawLoop();

            // 创建MediaStream
            this.stream = this.canvas.captureStream(30);
            this.isInitialized = true;

            console.log('小车视频源初始化成功:', this.carVideoUrl);
            return this.stream;

        } catch (error) {
            console.error('小车视频源初始化失败:', error);
            throw new Error(`无法连接到小车视频流: ${error.message}`);
        }
    }

    /**
     * 获取视频元素（用于MediaPipe处理）
     */
    getVideoElement() {
        return this.video;
    }

    /**
     * 获取MediaStream（用于录制）
     */
    getStream() {
        return this.stream;
    }

    /**
     * 检查连接状态
     */
    isConnected() {
        return this.isInitialized && 
               this.video && 
               !this.video.paused && 
               !this.video.ended &&
               this.video.readyState >= 2;
    }

    /**
     * 清理资源
     */
    cleanup() {
        if (this.video) {
            this.video.pause();
            this.video.src = '';
            this.video = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.isInitialized = false;
    }
}
```

然后在 `assessment.js` 中修改：
```javascript
// 在文件顶部导入
import { CarVideoSource } from './car_video_source.js';

// 替换原有的摄像头初始化代码
export async function initializeAssessment() {
    try {
        // 使用小车视频源替代本地摄像头
        const carVideoSource = new CarVideoSource('192.168.1.100'); // 替换为实际IP
        
        // 初始化小车视频源
        stream = await carVideoSource.initialize();
        video = carVideoSource.getVideoElement();
        
        // 将video元素附加到页面上（如果需要显示）
        const videoContainer = document.getElementById("video");
        if (videoContainer) {
            videoContainer.replaceWith(video);
            video.id = "video";
        }

        // 其余初始化代码保持不变...
        video.addEventListener("loadeddata", initEverything);
        
    } catch (error) {
        console.error('小车视频源连接失败:', error);
        alert('无法连接到小车摄像头，请检查网络连接和小车IP地址');
        
        // 失败时回退到本地摄像头
        console.log('回退到本地摄像头...');
        // 这里可以添加原有的getUserMedia代码作为备用方案
    }
}
```

### 3. 网络配置

#### 获取小车IP地址：
1. 启动小车系统：`python main.py`
2. 查看终端输出，找到类似这样的信息：
   ```
   Starting web server on http://0.0.0.0:5000
   Access the interface at:
     - http://127.0.0.1:5000
     - http://localhost:5000
   ```
3. 如果是有线连接，IP可能是 192.168.1.x 或 192.168.0.x

#### 测试连接：
在浏览器中访问 `http://小车IP:5000/video_feed`，应该能看到MJPEG视频流。

### 4. 故障排除

#### 常见问题：

1. **CORS错误**：
   - 确保小车端已添加flask-cors并重启
   - 检查浏览器控制台是否有跨域错误

2. **视频无法加载**：
   - 确认小车IP地址正确
   - 测试 `http://小车IP:5000` 是否可访问
   - 检查网络连接

3. **MediaPipe处理问题**：
   - 确保video元素有正确的宽高
   - 检查视频是否在播放状态

4. **录制功能异常**：
   - 验证canvas.captureStream()是否正常工作
   - 检查MediaStream tracks状态

### 5. 优化建议

1. **添加连接状态监控**：
   ```javascript
   // 定期检查连接状态
   setInterval(() => {
       if (!carVideoSource.isConnected()) {
           console.warn('小车视频连接丢失，尝试重连...');
           // 重连逻辑
       }
   }, 5000);
   ```

2. **添加加载指示器**：
   ```javascript
   // 显示加载状态
   const statusDiv = document.createElement('div');
   statusDiv.textContent = '正在连接小车摄像头...';
   document.body.appendChild(statusDiv);
   ```

3. **备用方案**：
   ```javascript
   // 连接失败时自动切换到本地摄像头
   catch (error) {
       console.log('小车连接失败，使用本地摄像头');
       stream = await navigator.mediaDevices.getUserMedia(constraints);
   }
   ```

## 测试验证

1. **启动小车系统**：`python main.py`
2. **打开SOFT3888项目**
3. **进入运动检测页面**
4. **验证视频源**：应该看到小车的摄像头画面而不是电脑摄像头
5. **测试功能**：姿态检测、录制等功能应正常工作

## 注意事项

- 网络延迟可能影响实时性，有线连接比无线更稳定
- 小车视频分辨率为640x480，如需其他分辨率需修改小车配置
- 确保小车有足够电量和网络连接稳定性
- 考虑添加错误处理和重连机制

## 总结

通过以上修改，您的SOFT3888项目将能够使用小车的摄像头作为输入源，实现远程人体运动分析。这为项目增加了移动性和灵活性，可以在不同位置和角度进行运动分析。