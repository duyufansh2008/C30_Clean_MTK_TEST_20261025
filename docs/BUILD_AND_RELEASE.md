# 源码、构建与发行包

## 当前交付边界

这个 Git 仓库是源码和历史构建记录，不是完整可刷包。缺失的 `images/super.img` 与 `rollback/super.img` 见 [Issue #1](https://github.com/lichengcheng2009/C30_Clean_MTK_TEST_20261025/issues/1)。没有找到可验证的作者公开下载入口，不能用其他 C30 ROM 替代。

`validation/*.json`、`sources/C30CleanLauncher.apk` 和固件 SHA256 是原始测试构建的历史记录。当前桌面源码优化不会自动进入历史 APK 或旧固件。本次构建结果在 `sources/build/`，需要作者取得原始输入后重建、验证 `super.img`，再更新发行包及镜像哈希。不要把模拟器测试 APK 刷入设备。

## 无需设备的源码检查

需要 64 位 Python 3.11+。Windows 自带打包依赖面向 x64；其他架构不能据此推定兼容。

```text
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
python tools/update_manifest.py --check
python tools/verify_files.py --source
```

`--source` 只跳过上述两个外置 super 镜像，其他清单项仍须存在且哈希一致；输出明确为 `SOURCE ONLY (not flashable)`。刷写与擦除入口始终使用完整校验，不接受源码检查结果代替。

修改文件并 `git add` 后运行 `python tools/update_manifest.py`。它以 Git 索引文件列表更新源码哈希；缺失的两个 super 镜像保留原有预期值，不会被静默删除。`.gitattributes` 禁止自动转换换行，保证 Windows/Linux 对相同提交校验相同字节。

## 独立构建桌面 APK

安装 JDK 8+（CI 使用 17）、Android SDK 平台 `platforms;android-30` 和构建工具 `build-tools;30.0.3`。从任意目录运行：

```text
python /path/to/repo/sources/build_launcher.py --sdk /path/to/android-sdk --java-home /path/to/jdk
```

也可使用 `ANDROID_SDK_ROOT` / `ANDROID_HOME` 与 `JAVA_HOME`。默认输出为仓库的 `sources/build/C30CleanLauncher.apk`。每次使用空临时目录，避免遗留 `.class` 混入 APK；脚本执行编译、DEX、对齐、签名及签名校验，任一步失败都停止，不覆盖历史 APK。

默认使用仓库公开的开发签名密钥，不能当作保密发行密钥。这保留原测试包的签名方式；新签名策略属于另一次发行迁移。

模拟器回归使用独立输出：

```text
python sources/build_launcher.py --sdk /path/to/android-sdk --test --output sources/build/C30LauncherChecks.apk
adb install -r sources/build/C30LauncherChecks.apk
adb shell am instrument -w com.fundot.p4bu/com.fundot.p4bu.LauncherChecks
```

必须出现 `c30_checks=passed`。检查实际 Activity 的应用缓存、图标缓存、格子复用、搜索及包变动刷新。它不验证 C30 厂商框架接口、USB 通信或真机性能。

## 固件重建所需输入

以下专用脚本仍针对原始 C30 备份，不能用于任意 ROM：

- 原始 RAW super/vbmeta：`work/original_extracted/GeekFlashTool_Readback_20261024222507755/`。
- 从原 super 提取的逻辑 system：`work/logical/system.img`。
- 原 system 文件树及 7-Zip `-slt` 清单：`work/system-files/system/`、`work/system-listing.txt`。
- 新构建桌面：`sources/build/C30CleanLauncher.apk`。
- Windows 的 Cygwin e2fsprogs：`work/tools/cygwin/usr/bin/`、`work/tools/cygwin/usr/sbin/`；Linux 使用 PATH 中的 `debugfs`、`e2fsck`。

从上述原始 super 精确提取 system 的物理范围为偏移 617611264、长度 1339117568；保留原输入，切勿在原件上原地修改。文件树及 inode 清单须来自同一份逻辑镜像。

运行 `python sources/modify_firmware.py` 后，使用 7-Zip `7z l -slt work/modified/system.img` 生成 UTF-8 的 `work/modified/system-listing.txt`，再运行 `python sources/verify_firmware.py`。这些脚本保留特定 ext4 格式和原始镜像大小限制，遇到其他布局必须拒绝。成功后才可把验证后的输出制作成新的发行镜像，并更新历史验证记录、APK、两套固件及清单。缺少原始输入时无法完成这一步，见 Issue #1。

## 连接与操作保护

1. 备份个人资料，并自行核实这就是原备份对应的设备、BL 已解锁。
2. 完整包校验通过后执行 `02_Read_Layout.cmd`。工具在当前 DA 连接内读取原始 GPT，验证 CRC、分区地址/大小和扇区大小，再读取 live MEID 并仅保存 SHA256 指纹到 `backup/device.json`。
3. 写入、回读、擦除时，在各自实际连接中重新读取 GPT 和 MEID，必须与登记相同。不能用历史 `gpt.bin` 或 MTKClient `.state` 的身份字段代替。`.state` 统一保存在 `backup/`，使分步命令能恢复同一 DA 会话；身份仍以实时读取为准。
4. 擦除前须输入 `ERASE <显示的12位指纹>`；输入错误、EOF、读取失败或设备变化均拒绝操作。没有无确认参数。
5. 写入、读取、擦除首个失败立即停止，进程非零退出。部分写入无法自动撤销，必须按回退流程恢复；错误退出码不代表原子操作。

设备指纹只防止登记后接错设备，**不证明首次登记的设备就是兼容硬件**。若 DA 不支持读取实时 MEID，会拒绝写入/擦除；仍需作者在真实 C30 验证。不要为了绕过保护而使用缓存 ID。

C30 的 `MTK.cmd` 只开放 `gpt`、`printgpt`、`r`、`w`、`e`、`reset`；写入限定包内 super/vbmeta，擦除限定原流程的四个分区。其他开发操作应使用独立的上游 MTKClient。基于上游源码的本地修改见 `tools/mtkclient/C30_LOCAL_PATCHES.md`。

## 制作完整发行包

取得作者可合法提供、与清单匹配的两个 super 镜像后，放入指定目录。若包含新版桌面，须先完成上述重建和验证、更新镜像哈希；不能沿用旧镜像冒充新版。

```text
python tools/verify_files.py
python tools/package_release.py /path/to/output/C30_Clean.zip
```

打包器先做完整文件校验，缺文件、哈希不符或目标 ZIP 已存在都会拒绝。通过后只打包清单文件和清单本身，使用 ZIP64；不会带入本机备份、回读、设备指纹和构建缓存。生成过程失败只清理临时输出，不留下半个发行包。

离线与模拟器检查通过不等于真机可刷。正式发布前仍需实际完成 DA 连接、刷写、逐分区回读、启动和硬件功能验证。
