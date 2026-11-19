---
name: c30-flash
description: Check GeekFlashTool backups, verify flash inputs, and guide authorized stock recovery and partition readback for the C30 with board tb8788p1_64_bsp and product TDC30-Ai10H. Use when assessing a C30 backup or preparing this repository for recovery.
---

# C30 固件校验与恢复

在仓库根目录工作。先确认机型和板级标识，以及备份是否对应实际目标设备。同名 C30 的其他硬件版本走各自的厂商流程。

1. **查源码。** 用 64 位 Python 3.11+ 运行 `python tools/verify_files.py --source`。记录当前 Git 提交和结果。此模式跳过两份本地 super 镜像，刷机准备状态需要完整包校验。
2. **查备份。** 在忽略目录 `work/` 中提取所需文件，运行 `python tools/check_original_backup.py <提取后的读回目录>`。该命令核对原始 super、vbmeta、预加载器及 scatter 的八个关键分区。`PASS` 后可将原始 super 放入 `rollback/super.img`。详细放置规则见[备份与恢复](references/backup-and-recovery.md)。
3. **评估刷机条件。** 运行 `python tools/verify_files.py`，并查阅根目录的[构建与发行说明](../../../docs/BUILD_AND_RELEASE.md)。完整包校验要求独立准备 `images/super.img` 和 `rollback/super.img`。缺件、哈希不符、设备不明、认证失败或实时布局不符时停止，报告具体原因。保持仓库清单的预期值。
4. **处理真机。** 先核对用户选定的设备、操作系统和授权连接方式。只读操作结束后报告设备布局结果。写入、擦除和重启各自需要用户明确授权。原厂回退与回读的具体检查点见[备份与恢复](references/backup-and-recovery.md)。认证或保护状态不满足时，交由设备管理员或厂商处理。

汇报时区分源码校验、备份匹配、完整包校验、实时设备检查、写后回读和真机启动的实际结果。把刷机日志、固件和设备身份数据留在本机。
