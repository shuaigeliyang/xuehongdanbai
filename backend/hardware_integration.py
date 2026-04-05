"""
血浆游离血红蛋白检测系统 - 硬件集成接口
作者: 哈雷酱大小姐 (￣▽￣)／
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import serial
import time
from enum import Enum


class DeviceStatus(Enum):
    """设备状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    BUSY = "busy"
    ERROR = "error"


class SpectrometerInterface(ABC):
    """光谱仪接口抽象类"""

    @abstractmethod
    def connect(self) -> bool:
        """连接设备"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接"""
        pass

    @abstractmethod
    def get_device_info(self) -> Dict:
        """获取设备信息"""
        pass

    @abstractmethod
    def set_wavelength(self, wavelength: int) -> bool:
        """设置波长"""
        pass

    @abstractmethod
    def measure_absorbance(self) -> float:
        """测量吸光度"""
        pass

    @abstractmethod
    def auto_zero(self) -> bool:
        """自动调零"""
        pass

    @abstractmethod
    def get_status(self) -> DeviceStatus:
        """获取设备状态"""
        pass


class SimulatedSpectrometer(SpectrometerInterface):
    """模拟光谱仪（用于测试）"""

    def __init__(self):
        self.status = DeviceStatus.DISCONNECTED
        self.current_wavelength = 375
        self.device_info = {
            "manufacturer": "哈雷酱科技",
            "model": "Simulated Spectrometer V1.0",
            "serial_number": "SIM-001"
        }

    def connect(self) -> bool:
        """连接设备"""
        self.status = DeviceStatus.CONNECTED
        return True

    def disconnect(self) -> bool:
        """断开连接"""
        self.status = DeviceStatus.DISCONNECTED
        return True

    def get_device_info(self) -> Dict:
        """获取设备信息"""
        return self.device_info

    def set_wavelength(self, wavelength: int) -> bool:
        """设置波长"""
        if wavelength not in [375, 405, 450]:
            return False
        self.current_wavelength = wavelength
        return True

    def measure_absorbance(self) -> float:
        """测量吸光度（模拟）"""
        import random
        base_value = 0.1 + (self.current_wavelength - 375) * 0.01
        noise = random.gauss(0, 0.005)
        return max(0, base_value + noise)

    def auto_zero(self) -> bool:
        """自动调零"""
        time.sleep(1)  # 模拟调零时间
        return True

    def get_status(self) -> DeviceStatus:
        """获取设备状态"""
        return self.status


class SerialSpectrometer(SpectrometerInterface):
    """串口光谱仪（真实硬件）"""

    def __init__(self, port: str = "COM3", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.status = DeviceStatus.DISCONNECTED
        self.device_info = {}

    def connect(self) -> bool:
        """连接设备"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.status = DeviceStatus.CONNECTED

            # 读取设备信息
            self._read_device_info()

            return True
        except Exception as e:
            print(f"连接失败: {e}")
            self.status = DeviceStatus.ERROR
            return False

    def disconnect(self) -> bool:
        """断开连接"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            self.status = DeviceStatus.DISCONNECTED
            return True
        except Exception as e:
            print(f"断开连接失败: {e}")
            return False

    def _read_device_info(self):
        """读取设备信息"""
        if not self.serial_connection:
            return

        try:
            # 发送获取设备信息命令
            self.serial_connection.write(b'INFO?\n')
            response = self.serial_connection.readline().decode().strip()

            # 解析响应（示例格式）
            if response:
                parts = response.split(',')
                if len(parts) >= 3:
                    self.device_info = {
                        "manufacturer": parts[0],
                        "model": parts[1],
                        "serial_number": parts[2]
                    }
        except Exception as e:
            print(f"读取设备信息失败: {e}")

    def get_device_info(self) -> Dict:
        """获取设备信息"""
        return self.device_info

    def set_wavelength(self, wavelength: int) -> bool:
        """设置波长"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return False

        try:
            command = f'WAVE {wavelength}\n'
            self.serial_connection.write(command.encode())

            # 等待响应
            response = self.serial_connection.readline().decode().strip()
            return response == "OK"
        except Exception as e:
            print(f"设置波长失败: {e}")
            return False

    def measure_absorbance(self) -> float:
        """测量吸光度"""
        if not self.serial_connection or not self.serial_connection.is_open:
            raise Exception("设备未连接")

        try:
            # 发送测量命令
            self.serial_connection.write(b'MEASURE\n')

            # 读取响应
            response = self.serial_connection.readline().decode().strip()
            absorbance = float(response)

            return absorbance
        except Exception as e:
            print(f"测量失败: {e}")
            raise

    def auto_zero(self) -> bool:
        """自动调零"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return False

        try:
            self.serial_connection.write(b'ZERO\n')
            time.sleep(2)  # 等待调零完成

            response = self.serial_connection.readline().decode().strip()
            return response == "ZERO_OK"
        except Exception as e:
            print(f"调零失败: {e}")
            return False

    def get_status(self) -> DeviceStatus:
        """获取设备状态"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return DeviceStatus.DISCONNECTED
        return self.status


class SpectrometerController:
    """光谱仪控制器"""

    def __init__(self, device: SpectrometerInterface):
        self.device = device
        self.is_connected = False

    def connect(self) -> Dict:
        """连接设备"""
        success = self.device.connect()
        self.is_connected = success

        if success:
            return {
                "status": "success",
                "message": "设备连接成功",
                "device_info": self.device.get_device_info()
            }
        else:
            return {
                "status": "error",
                "message": "设备连接失败"
            }

    def disconnect(self) -> Dict:
        """断开连接"""
        success = self.device.disconnect()
        self.is_connected = False

        return {
            "status": "success" if success else "error",
            "message": "设备已断开" if success else "断开连接失败"
        }

    def perform_measurement(self) -> Dict:
        """执行完整的三波长测量"""
        if not self.is_connected:
            return {
                "status": "error",
                "message": "设备未连接"
            }

        try:
            # 自动调零
            self.device.auto_zero()

            # 测量三个波长
            wavelengths = [375, 405, 450]
            absorbance = {}

            for wl in wavelengths:
                self.device.set_wavelength(wl)
                time.sleep(0.5)  # 等待波长切换稳定
                absorbance[wl] = self.device.measure_absorbance()

            return {
                "status": "success",
                "absorbance": {
                    "a375": round(absorbance[375], 4),
                    "a405": round(absorbance[405], 4),
                    "a450": round(absorbance[450], 4)
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"测量失败: {str(e)}"
            }

    def get_device_status(self) -> Dict:
        """获取设备状态"""
        return {
            "is_connected": self.is_connected,
            "status": self.device.get_status().value,
            "device_info": self.device.get_device_info() if self.is_connected else {}
        }


# 工厂函数
def create_spectrometer(device_type: str = "simulated", **kwargs) -> SpectrometerController:
    """创建光谱仪控制器"""
    if device_type == "simulated":
        device = SimulatedSpectrometer()
    elif device_type == "serial":
        device = SerialSpectrometer(
            port=kwargs.get("port", "COM3"),
            baudrate=kwargs.get("baudrate", 9600)
        )
    else:
        raise ValueError(f"不支持的设备类型: {device_type}")

    return SpectrometerController(device)
