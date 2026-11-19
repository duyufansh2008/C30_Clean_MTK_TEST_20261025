# 备份与恢复

## 用途和输入

项目记录的原始备份来自 GeekFlashTool 读回。已核验过一份包含 45 个文件的归档，原始 `super.img`、`vbmeta.img` 和预加载器与仓库清单逐字节匹配，原始 scatter 的八个关键布局项也匹配。该归档缺少 `userdata.img`，个人文件需另行备份。

在 `work/` 中对只读备份操作。提取 `super.img`、`vbmeta.img`、`preloader_tb8788p1_64_bsp.bin` 和 `MT6771_Android_scatter.txt` 到同一目录。把该目录传给 `tools/check_original_backup.py`，路径包含空格时加引号。该脚本只读取本地文件。归档格式和解压工具的兼容性以实际测试为准。

| 备份内容 | 通过校验后的用途 |
| --- | --- |
| `super.img` | 复制到 `rollback/super.img`。保持 `images/super.img` 使用单独准备和核验的项目镜像。 |
| `vbmeta.img` | 与已跟踪的 `rollback/vbmeta.img` 核对。 |
| `preloader_tb8788p1_64_bsp.bin` | 与 `tools/device_preloader.bin` 核对。 |
| `MT6771_Android_scatter.txt` | 离线核对地址、大小和存储区域。真机操作要求实时 GPT。 |
| 其余分区 | 原样保留在本机备份，按本设备的厂商恢复方案使用。 |

## Windows 原厂回退

确认已按仓库要求备齐本地输入，确认已有受授权的设备连接，并使用仓库的标准安全校验。以仓库根目录为工作目录，逐步核对返回码和输出。连接或认证失败时在当前步骤停止。

1. `01_Verify_Files.cmd` 完整包通过后，运行 `02_Read_Layout.cmd`。核对当前设备实时 GPT，并由用户确认这是目标设备。登记的指纹用于防止后续接错设备。
2. 经用户授权恢复原厂镜像后运行 `90_Restore_Original.cmd`。它使用 `rollback/` 下的原始 super 和 vbmeta。任何失败都需要先保留日志并核对分区状态。
3. 写入成功后运行 `91_Check_Original_Readback.cmd`。必须看到 `super.img` 与 `vbmeta.img` 两项逐文件回读校验通过。
4. 如用户还需要恢复出厂设置，由用户独立决定并通过设备原厂 Recovery 完成。确认个人数据已另行备份。经用户授权后重启，再检查启动、触摸、Wi-Fi、旋转和相机。

Windows 入口和连接要求见仓库现有说明。Linux 可运行离线备份核验与源码测试。现场可用性以授权的设备连接和实际回读结果为准。
