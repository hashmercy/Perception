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
  safe_run "ROS_DISTRO (env)" bash -lc "echo \${ROS_DISTRO:-unset}"
  safe_run "ROS_VERSION (env)" bash -lc "echo \${ROS_VERSION:-unset}"
  safe_run "ROS_PYTHON_VERSION (env)" bash -lc "echo \${ROS_PYTHON_VERSION:-unset}"
  safe_run "ros2 path" bash -lc "which ros2"
  safe_run "ros2 cli package version" bash -lc "dpkg -l | awk '/^ii  ros-[a-z0-9-]+-ros2cli/ {print \$2\" \"\$3}'"
  safe_run "ROS2 packages (dpkg)" bash -lc "dpkg -l | awk '/^ii  ros-(humble|jazzy|iron|foxy|rolling)-(ros-base|desktop|desktop-full)/ {print \$2\" \"\$3}'"
  safe_run "Python" python3 --version
  safe_run "Colcon" bash -lc "colcon --help | sed -n '1,3p'"
  safe_run "RMW implementation" bash -lc "echo \${RMW_IMPLEMENTATION:-unset}"
  safe_run "ROS domain id" bash -lc "echo \${ROS_DOMAIN_ID:-unset}"
} >"${OUT_FILE}"

rm -f /tmp/_env_check_tmp
echo "Environment check saved: ${OUT_FILE}"
