import torch

print("PyTorch 版本:", torch.__version__)
print("CUDA 是否可用:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("当前显卡名称:", torch.cuda.get_device_name(0))
    print("显卡数量:", torch.cuda.device_count())
else:
    print("❌ 警告：未检测到显卡，请检查驱动和安装指令！")