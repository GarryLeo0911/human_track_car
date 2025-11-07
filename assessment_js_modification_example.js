/**
 * SOFT3888项目 assessment.js 修改示例
 * 
 * 这个文件展示了如何在assessment.js中集成小车视频源
 * 
 * 修改步骤：
 * 1. 复制 car_video_source.js 到 SOFT3888_F16_02_P15/static/js/
 * 2. 在 assessment.js 顶部添加导入语句
 * 3. 修改 initializeAssessment 函数中的摄像头获取部分
 */

// ===============================================
// 第一步：在 assessment.js 文件顶部添加导入
// ===============================================

// 在 assessment.js 的最顶部添加以下导入语句：
import { CarVideoSource } from './car_video_source.js';

// ===============================================
// 第二步：修改 initializeAssessment 函数
// ===============================================

export async function initializeAssessment() {
    // 保持原有的webcam注释
    // webcam
    try {
        // === 小车视频源集成 - 开始 ===
        
        // 配置小车IP (需要根据实际情况修改)
        const CAR_IP = '192.168.1.100'; // 请替换为实际的小车IP地址
        const USE_CAR_VIDEO = true;     // 设为false可回退到本地摄像头
        
        if (USE_CAR_VIDEO) {
            try {
                console.log('🚗 尝试连接小车视频源...');
                
                // 创建小车视频源实例
                const carVideoSource = new CarVideoSource(CAR_IP);
                
                // 初始化小车视频源
                const { video: carVideo, stream: carStream } = await carVideoSource.initialize();
                
                // 替换页面上的video元素
                const existingVideoElement = document.getElementById("video");
                if (existingVideoElement && existingVideoElement.parentNode) {
                    // 保持原有的id和样式
                    carVideo.id = "video";
                    carVideo.className = existingVideoElement.className;
                    existingVideoElement.parentNode.replaceChild(carVideo, existingVideoElement);
                } else {
                    // 如果没有现有元素，直接设置id
                    carVideo.id = "video";
                }
                
                // 设置全局变量
                video = carVideo;
                stream = carStream;
                
                console.log('✅ 小车视频源连接成功!');
                console.log(`   分辨率: ${video.videoWidth}x${video.videoHeight}`);
                console.log(`   视频URL: http://${CAR_IP}:5000/video_feed`);
                
                // 添加连接状态监控
                const monitorConnection = () => {
                    if (!carVideoSource.isConnected()) {
                        console.warn('⚠️ 小车视频连接可能已断开');
                        // 这里可以添加重连逻辑或用户提示
                    }
                };
                
                // 每5秒检查一次连接状态
                setInterval(monitorConnection, 5000);
                
                // 成功标记
                window.usingCarVideo = true;
                window.carVideoSource = carVideoSource;
                
            } catch (carError) {
                console.error('❌ 小车视频源连接失败:', carError);
                
                // 用户友好的错误提示
                const errorMessage = `无法连接到小车摄像头:\n${carError.message}\n\n请检查：\n1. 小车是否已启动 (python main.py)\n2. 网络连接是否正常\n3. IP地址是否正确: ${CAR_IP}\n4. 访问 http://${CAR_IP}:5000 确认小车服务运行\n\n将自动回退到本地摄像头...`;
                
                alert(errorMessage);
                
                // 抛出错误以触发回退到本地摄像头
                throw carError;
            }
        } else {
            throw new Error('小车视频已禁用，使用本地摄像头');
        }
        
        // === 小车视频源集成 - 结束 ===
        
    } catch (error) {
        // 回退到原有的本地摄像头逻辑
        console.log('🔄 回退到本地摄像头...');
        
        // Check if getUserMedia exists
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera access is not supported in this browser');
        }
        
        const constraints = {
            audio: false,
            video: {
                facingMode: 'user',
                frameRate: { ideal: 30, max: 60 },
                // 其他原有的约束...
            }
        };

        // video global vars
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video = document.getElementById("video");
        video.srcObject = stream;
        
        console.log('✅ 本地摄像头初始化完成');
        window.usingCarVideo = false;
    }

    // Detect camera FPS after stream is established
    detectCameraFPS();

    // rest of init, frame loop
    video.addEventListener("loadeddata", initEverything);
    
    // 后续代码保持不变...
}

// ===============================================
// 第三步：添加页面卸载时的清理函数（可选）
// ===============================================

// 在 assessment.js 文件末尾添加以下代码：

// 页面卸载时清理资源
window.addEventListener('beforeunload', () => {
    if (window.carVideoSource) {
        console.log('🧹 清理小车视频资源...');
        window.carVideoSource.cleanup();
    }
});

// ===============================================
// 使用说明
// ===============================================

/*
修改完成后的使用流程：

1. 启动小车系统：
   cd /path/to/human_track_car
   python main.py

2. 查看小车启动日志，获取IP地址，例如：
   Starting web server on http://0.0.0.0:5000
   Access the interface at:
     - http://192.168.1.100:5000  <-- 这是需要的IP地址

3. 修改上面代码中的 CAR_IP 变量为实际IP地址

4. 在浏览器中测试视频流：
   访问 http://小车IP:5000/video_feed
   应该能看到 MJPEG 视频流

5. 运行 SOFT3888 项目，视频输入应该来自小车摄像头

故障排除：
- 如果连接失败，系统会自动回退到本地摄像头
- 检查浏览器控制台的详细错误信息
- 确认网络连接和防火墙设置
- 测试小车Web界面是否可访问：http://小车IP:5000
*/