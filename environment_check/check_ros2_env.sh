#!/usr/bin/env bash
set -euo pipefail

# This script collects ROS2 and system environment facts so two machines
# can be compared quickly. Output files are stored in environment_check/.

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${BASE_DIR}/environment_check"
HOST="$(hostname | tr ' ' '_' | tr '/' '_')"
TS="$(date +%Y%m%d_%H%M%S)"
OUT_FILE="${OUT_DIR}/env_${HOST}_${TS}.txt"

mkdir -p "${OUT_DIR}"

safe_run() {
  local title="$1"
  shift
  echo ""
  echo "## ${title}"
  if "$@" >/tmp/_env_check_tmp 2>&1; then
    cat /tmp/_env_check_tmp
  else
    echo "(command failed)"
    cat /tmp/_env_check_tmp
  fi
}

{
  echo "# ROS2 Environment Check"
  echo ""
  echo "- generated_at: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "- hostname: ${HOST}"
  echo "- user: $(whoami)"
  echo "- pwd: $(pwd)"

  safe_run "OS" uname -a
  safe_run "Linux Release" bash -lc "if [ -f /etc/os-release ]; then cat /etc/os-release; else echo 'no /etc/os-release'; fi"
  safe_run "ROS_DISTRO (env)" bash -lc "printenv ROS_DISTRO"
  safe_run "ROS_VERSION (env)" bash -lc "printenv ROS_VERSION"
  safe_run "ROS_PYTHON_VERSION (env)" bash -lc "printenv ROS_PYTHON_VERSION"
  safe_run "ros2 path" bash -lc "which ros2"
  safe_run "ros2 --version" bash -lc "ros2 --version"
  safe_run "ROS2 packages (dpkg)" bash -lc "dpkg -l | rg '^ii  ros-(humble|jazzy|iron|foxy|rolling)-(ros-base|desktop|desktop-full)'"
  safe_run "Python" python3 --version
  safe_run "Colcon" bash -lc "colcon --version"
  safe_run "RMW implementation" bash -lc "printenv RMW_IMPLEMENTATION"
  safe_run "ROS domain id" bash -lc "printenv ROS_DOMAIN_ID"
} >"${OUT_FILE}"

rm -f /tmp/_env_check_tmp
echo "Environment check saved: ${OUT_FILE}"
