/**
 * 小车视频源集成模块
 * 用于将小车的视频流作为SOFT3888项目的输入源
 * 
 * 使用方法：
 * 1. 将此文件保存到 SOFT3888_F16_02_P15/static/js/car_video_source.js
 * 2. 在 assessment.js 中导入并使用
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
     * 初始化小车视频源，替代getUserMedia
     * @returns {Promise<{video: HTMLVideoElement, stream: MediaStream}>}
     */
    async initialize() {
        try {
            console.log('正在连接小车视频源:', this.carVideoUrl);

            // 创建video元素接收小车视频流
            this.video = document.createElement('video');
            this.video.crossOrigin = 'anonymous';
            this.video.autoplay = true;
            this.video.muted = true;
            this.video.playsInline = true;
            this.video.style.width = '100%';
            this.video.style.height = '100%';

            // 设置视频源
            this.video.src = this.carVideoUrl;

            // 等待视频加载完成
            await new Promise((resolve, reject) => {
                const loadedHandler = () => {
                    this.video.removeEventListener('loadedmetadata', loadedHandler);
                    this.video.removeEventListener('error', errorHandler);
                    resolve();
                };
                
                const errorHandler = (e) => {
                    this.video.removeEventListener('loadedmetadata', loadedHandler);
                    this.video.removeEventListener('error', errorHandler);
                    reject(new Error(`视频加载失败: ${e.message || '未知错误'}`));
                };

                this.video.addEventListener('loadedmetadata', loadedHandler);
                this.video.addEventListener('error', errorHandler);

                // 10秒超时
                setTimeout(() => {
                    this.video.removeEventListener('loadedmetadata', loadedHandler);
                    this.video.removeEventListener('error', errorHandler);
                    reject(new Error('视频加载超时'));
                }, 10000);
            });

            console.log('小车视频加载成功:', this.video.videoWidth, 'x', this.video.videoHeight);

            // 创建canvas用于生成MediaStream（用于录制功能）
            this.canvas = document.createElement('canvas');
            this.canvas.width = this.video.videoWidth || 640;
            this.canvas.height = this.video.videoHeight || 480;
            
            const ctx = this.canvas.getContext('2d');

            // 持续将视频帧绘制到canvas
            const drawFrame = () => {
                if (this.video && !this.video.paused && !this.video.ended) {
                    ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
                }
                if (!this.isInitialized) return; // 停止循环
                requestAnimationFrame(drawFrame);
            };

            // 等视频开始播放后启动绘制循环
            this.video.addEventListener('playing', () => {
                console.log('小车视频开始播放');
                drawFrame();
            });

            // 创建MediaStream用于录制
            this.stream = this.canvas.captureStream(30); // 30 FPS
            this.isInitialized = true;

            return {
                video: this.video,
                stream: this.stream
            };

        } catch (error) {
            console.error('小车视频源初始化失败:', error);
            this.cleanup();
            throw error;
        }
    }

    /**
     * 检查连接状态
     */
    isConnected() {
        return this.isInitialized && 
               this.video && 
               this.video.readyState >= 2 &&
               !this.video.paused && 
               !this.video.ended;
    }

    /**
     * 获取状态信息
     */
    getStatus() {
        if (!this.video) return '未初始化';
        if (this.video.ended) return '视频已结束';
        if (this.video.paused) return '视频暂停';
        if (this.video.readyState < 2) return '加载中...';
        return '正常';
    }

    /**
     * 清理资源
     */
    cleanup() {
        this.isInitialized = false;
        
        if (this.video) {
            this.video.pause();
            this.video.src = '';
            this.video.load(); // 强制停止加载
            this.video = null;
        }
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        this.canvas = null;
        console.log('小车视频源已清理');
    }
}

/**
 * 修改SOFT3888项目assessment.js的示例代码
 * 
 * 在assessment.js的initializeAssessment函数中，替换原有的getUserMedia代码：
 * 
 * // === 原代码 (删除或注释掉) ===
 * // stream = await navigator.mediaDevices.getUserMedia(constraints);
 * // video = document.getElementById("video");
 * // video.srcObject = stream;
 * 
 * // === 新代码 (替换为以下内容) ===
 * try {
 *     // 使用小车视频源
 *     const carVideoSource = new CarVideoSource('192.168.1.100'); // 替换为实际小车IP
 *     const { video: carVideo, stream: carStream } = await carVideoSource.initialize();
 *     
 *     // 替换页面上的video元素
 *     const existingVideo = document.getElementById("video");
 *     if (existingVideo && existingVideo.parentNode) {
 *         carVideo.id = "video";
 *         existingVideo.parentNode.replaceChild(carVideo, existingVideo);
 *     }
 *     
 *     // 设置全局变量
 *     video = carVideo;
 *     stream = carStream;
 *     
 *     console.log('✅ 小车视频源连接成功');
 * 
 * } catch (error) {
 *     console.error('❌ 小车视频源连接失败:', error);
 *     alert(`无法连接小车摄像头: ${error.message}\n\n请检查：\n1. 小车是否已启动 (python main.py)\n2. 网络连接是否正常\n3. IP地址是否正确`);
 *     
 *     // 回退到本地摄像头
 *     console.log('🔄 回退到本地摄像头...');
 *     stream = await navigator.mediaDevices.getUserMedia(constraints);
 *     video = document.getElementById("video");
 *     video.srcObject = stream;
 * }
 */