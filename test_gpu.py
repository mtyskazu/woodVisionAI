import torch
import torch.backends.cudnn as cudnn

print(f"--- GPU Check ---")
print(f"1. CUDA version:    {torch.version.cuda}")
print(f"2. Device name:     {torch.cuda.get_device_name(0)}")
print(f"3. cuDNN version:   {cudnn.version()}")
print(f"4. cuDNN enabled:   {cudnn.enabled}")

# 実際に小さな計算をGPUで走らせてみる
x = torch.randn(1, 3, 224, 224).cuda()
model = torch.nn.Conv2d(3, 64, 3).cuda()
output = model(x)
print(f"5. Test Calculation: Success (Output shape: {output.shape})")