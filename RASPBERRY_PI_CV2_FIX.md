# 树莓派上cv2模块缺失解决方案

在树莓派OS上运行`main.py`时出现"没有cv2"错误，这是因为OpenCV没有正确安装。以下是几种解决方案：

## 方案一：使用系统包管理器安装（推荐）

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装OpenCV系统包
sudo apt install python3-opencv

# 验证安装
python3 -c "import cv2; print('OpenCV version:', cv2.__version__)"
```

## 方案二：使用自动安装脚本

```bash
# 在项目目录中运行
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh

# 重启后测试
sudo reboot
python3 test_environment.py
```

## 方案三：手动pip安装（可能很慢）

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装预编译的OpenCV包
pip install opencv-python

# 或者安装精简版
pip install opencv-python-headless
```

## 方案四：如果仍然失败

有时树莓派需要额外的系统依赖：

```bash
# 安装构建依赖
sudo apt install -y \
    python3-dev \
    python3-numpy \
    libjpeg-dev \
    libtiff5-dev \
    libjasper-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran

# 然后重新安装OpenCV
sudo apt install python3-opencv
```

## 测试安装

运行测试脚本验证所有依赖：

```bash
python3 test_environment.py
```

## 常见问题

1. **虚拟环境中找不到cv2**：
   - 如果使用系统包安装的OpenCV，需要使用`--system-site-packages`创建虚拟环境
   ```bash
   python3 -m venv --system-site-packages venv
   ```

2. **权限错误**：
   - 确保用户在video组中：`sudo usermod -a -G video $USER`
   - 注销重新登录

3. **摄像头权限**：
   ```bash
   # 启用摄像头接口
   sudo raspi-config nonint do_camera 0
   sudo reboot
   ```

## 验证完整环境

所有依赖安装完成后，运行：

```bash
python3 main.py
```

如果仍有问题，请提供具体的错误信息。