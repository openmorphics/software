# 🚀 Installation Guide

Complete installation instructions for EventFlow across different platforms and use cases.

## 📋 **System Requirements**

### **Minimum Requirements**
- **Python**: 3.9+ (3.9, 3.10, 3.11 recommended)
- **Operating System**: Linux, macOS, Windows (via WSL)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space

### **Recommended Hardware**
- **CPU**: Multi-core processor (4+ cores)
- **RAM**: 16GB+ for development, 8GB+ for production
- **GPU**: NVIDIA GPU with CUDA support (optional, for GPU backend)
- **Storage**: SSD with 10GB+ free space

## 🐧 **Linux Installation**

### **Ubuntu/Debian**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential git cmake

# Install optional dependencies
sudo apt install -y libssl-dev pkg-config

# Verify Python version
python3 --version  # Should be 3.9+
```

### **Red Hat/CentOS/Fedora**
```bash
# Install Python and development tools
sudo dnf install -y python3 python3-pip python3-devel
sudo dnf install -y gcc gcc-c++ make git cmake

# Install optional dependencies
sudo dnf install -y openssl-devel pkgconfig

# Verify Python version
python3 --version
```

## 🍎 **macOS Installation**

### **Using Homebrew (Recommended)**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install development tools
brew install cmake git

# Add Python to PATH
echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify installation
python3 --version
pip3 --version
```

### **Using Xcode Command Line Tools**
```bash
# Install Xcode command line tools
xcode-select --install

# Install Python via official installer from python.org
# Or use pyenv for version management
curl https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
source ~/.zshrc

pyenv install 3.11.0
pyenv global 3.11.0
```

## 🪟 **Windows Installation**

### **Using WSL (Recommended)**
```powershell
# Enable WSL feature
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Install Ubuntu from Microsoft Store
# Then follow Linux installation instructions above
```

### **Native Windows (Experimental)**
```powershell
# Install Python from python.org (3.9+)
# Install Git for Windows
# Install Visual Studio Build Tools

# Note: Native Windows support is experimental
# WSL is strongly recommended for full functionality
```

## 📦 **EventFlow Installation**

### **Method 1: Editable Installation (Recommended for Development)**

```bash
# Clone the repository
git clone https://github.com/your-org/eventflow.git
cd eventflow

# Create virtual environment
python3 -m venv eventflow-env
source eventflow-env/bin/activate  # Linux/macOS
# or: eventflow-env\Scripts\activate  # Windows

# Install core components
pip install -e ./eventflow-core
pip install -e ./eventflow-sal
pip install -e ./eventflow-backends
pip install -e ./eventflow-cli
pip install -e ./eventflow-modules

# Verify installation
ef --help
```

### **Method 2: PyPI Installation (For Users)**

```bash
# Install from PyPI (when available)
pip install eventflow

# Or install specific components
pip install eventflow-core eventflow-sal eventflow-cli
```

### **Method 3: Docker Installation**

```bash
# Pull Docker image (when available)
docker pull eventflow/eventflow:latest

# Run container
docker run -it eventflow/eventflow:latest ef --help
```

## ⚡ **Backend-Specific Installation**

### **CPU Backend (Always Available)**
```bash
# CPU backend is included with eventflow-core
pip install -e ./eventflow-core
```

### **GPU Backend (Optional)**
```bash
# Install CUDA (Linux)
sudo apt install -y nvidia-cuda-toolkit

# Install GPU backend
pip install -e ./eventflow-backends[gpu]

# Verify GPU support
ef run --backend gpu-sim --help
```

### **Neuromorphic Hardware Backends**

#### **Intel Loihi**
```bash
# Install NxSDK (requires NDA and special access)
# Contact Intel for NxSDK installation

pip install -e ./eventflow-backends[loihi]
```

#### **SpiNNaker**
```bash
# Install sPyNNaker
pip install spyNNaker

pip install -e ./eventflow-backends[spinnaker]
```

#### **SynSense Xylo/Speck**
```bash
# Install Rockpool
pip install rockpool

pip install -e ./eventflow-backends[synsense]
```

## 🔧 **Optional Dependencies**

### **Performance Optimization**
```bash
# NumPy for SAL acceleration
pip install numpy

# SciPy for advanced signal processing
pip install scipy

# Matplotlib for visualization
pip install matplotlib
```

### **Development Tools**
```bash
# Testing framework
pip install pytest pytest-cov

# Code quality
pip install black flake8 mypy

# Documentation
pip install sphinx sphinx-rtd-theme
```

### **Domain-Specific Libraries**
```bash
# Computer vision
pip install opencv-python

# Audio processing
pip install librosa

# Scientific computing
pip install pandas scikit-learn
```

## 🧪 **Testing Installation**

### **Basic Functionality Test**
```bash
# Test CLI
ef --help

# Test core functionality
ef --json validate --eir examples/vision_corner_tracking/eir.json

# Test SAL
ef --json sal-stream --uri "vision.dvs://file?format=jsonl&path=examples/vision_corner_tracking/traces/inputs/corner_sample.jsonl" --out test.jsonl
```

### **Domain-Specific Tests**
```bash
# Test healthcare domain
ef run --eir examples/medical_bio_signals/hrv_analysis.eir.json --backend cpu-sim --input examples/medical_bio_signals/ecg_sample.jsonl --trace-out test_hrv.trace.jsonl

# Test autonomous domain
ef run --eir examples/autonomous_vehicles/lidar_obstacle_detection.eir.json --backend cpu-sim --input examples/autonomous_vehicles/lidar_sample.jsonl --trace-out test_lidar.trace.jsonl
```

### **Performance Tests**
```bash
# Test native acceleration
export EF_NATIVE=1
ef run --eir examples/vision_corner_tracking/eir.json --backend cpu-sim --input examples/vision_corner_tracking/traces/inputs/corner_sample.jsonl --trace-out native_test.trace.jsonl

# Test GPU backend (if available)
ef run --eir examples/vision_corner_tracking/eir.json --backend gpu-sim --input examples/vision_corner_tracking/traces/inputs/corner_sample.jsonl --trace-out gpu_test.trace.jsonl
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Enable native Rust acceleration
export EF_NATIVE=1

# Set default backend
export EF_BACKEND=gpu-sim

# Enable telemetry
export EF_TELEMETRY=1

# Set log level
export EF_LOG_LEVEL=DEBUG
```

### **Configuration File**
```bash
# Create config file
ef config --set default.backend cpu-sim
ef config --set native.acceleration true
ef config --set telemetry.enabled true

# View current config
ef config --list
```

## 🐛 **Troubleshooting Installation**

### **Common Issues**

**"ef: command not found"**
```bash
# Ensure CLI is installed and in PATH
which ef
pip show eventflow-cli

# Try using python module
python -m eventflow_cli.main --help
```

**"ImportError: No module named 'eventflow_core'"**
```bash
# Check installation
pip list | grep eventflow

# Reinstall core components
pip install -e ./eventflow-core
```

**"Backend not available"**
```bash
# List available backends
ef run --backend --list

# Check backend installation
pip show eventflow-backends
```

**"Rust acceleration not working"**
```bash
# Check Rust installation
rustc --version

# Build native components
cd eventflow-core && python -m pip install -U maturin && python -m maturin develop -r
```

### **Platform-Specific Issues**

**macOS: "clang: error: unsupported option '-fopenmp'"**
```bash
# Install OpenMP support
brew install libomp
export CPPFLAGS="-I/usr/local/opt/libomp/include"
export LDFLAGS="-L/usr/local/opt/libomp/lib"
```

**Linux: "No CUDA installation detected"**
```bash
# Verify CUDA installation
nvidia-smi
nvcc --version

# Install CUDA toolkit
sudo apt install nvidia-cuda-toolkit
```

## 📞 **Support**

- **Installation Issues**: Check [Troubleshooting Guide](../README.md#troubleshooting-guide)
- **Platform Support**: GitHub Issues with your OS/Python versions
- **Community Help**: EventFlow community forums

---

**🎉 Installation complete?** Head to the [Quick Start Guide](../README.md#quick-start) to start building neuromorphic applications!