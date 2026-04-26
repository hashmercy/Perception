# Environment Check

用于在两台电脑上采集 ROS2 环境信息并进行对比。

## 使用方法

在仓库根目录执行：

```bash
./environment_check/check_ros2_env.sh
```

执行后会在 `environment_check/` 下生成报告文件：

- `env_<hostname>_<timestamp>.txt`

## 对比重点

- `ROS_DISTRO`
- `ros2 --version`
- `which ros2` 路径
- `dpkg` 中安装的 `ros-<distro>-ros-base/desktop`
- `RMW_IMPLEMENTATION`
- `ROS_DOMAIN_ID`
