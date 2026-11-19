C30 皆成管控清除包（MTK 测试构建）
制作日期：2026-10-25

本包已完成离线构建、文件系统检查和差异核对；尚未在你的平板上试刷、启动或验证触摸/相机/网络。它具有可供 MTK 写入的 RAW 分区镜像和刷入脚本，但不能据此保证真机可启动或绝对无损。
适用前提：就是所提供备份对应的这台 C30，BL 已解锁，并接受清空用户数据。不要给其他型号或其他硬件版本的“C30”使用。

一、检测与处理结果

1. 原备份中的主程序位于：
   super.img -> system 逻辑分区 -> /system/priv-app/ROM_523031602_GENERAL_DET/ROM_523031602_GENERAL_DET.apk
   原包名：com.fundot.p4bu
   原应用名：皆成守护孩子端
   版本：ROM_523031602_GENERAL_DET / 523031602
   系统为 Android 11 / SDK 30；板级标识 tb8788p1_64_bsp，产品标识含 TDC30-Ai10H。

2. 原固件不是单独一个管控 APK：framework.jar 中的 Instrumentation.newApplication 会加载 com.fundot.p4bu.ii.Monitor，services.jar 的 SystemServer 也会加载它；ResolverActivity 还指向该包里的 app.lawnchair.LawnchairLauncher。

3. 处理方式：彻底替换原管控 APK 的实现，提供新的 C30 基础桌面。为避免改动 Android 核心框架和预编译启动镜像，保留相同包名、相同桌面类名，以及两个无操作兼容方法 Monitor.init(Context) 和 Monitor.sysInit(Context)。
   因此，在系统框架或包列表中搜索 com.fundot.p4bu 仍会命中；该名称现在对应本地编译的新桌面，不是原管控实现。没有宣称固件已完全不存在这些字符串，也没有把它伪装为原厂纯净 ROM。

4. 新 APK 只有基础桌面、应用列表、搜索和打开设置。无联网权限、设备管理员、VPN、无障碍服务、开机广播或后台服务。源码在 sources/launcher/。

5. 已移除原 APK 旁的 8 个库文件，以及 /system/lib 与 /system/lib64 下各自的 libp4bu.so、libsandhook.so、libsandhook-native.so，共 14 个库文件。已清除对应特权授权块和公共库列表条目，并将空闲块清零，避免旧代码留在释放后的空间中。

6. 新 system 文件系统保留原有 UID/GID、权限及其他文件的 SELinux 信息；3 个替换文件均为 root:root、0644、u:object_r:system_file:s0。完整 e2fsck 检查退出码为 0；其余 3669 个普通文件逐个 SHA256 比较相同。product、vendor、LP 元数据及 system 范围之外所有 super 字节保持原样。

7. vbmeta.img 从原备份复制，仅将偏移 123 的字节改为 3（AVB flags=3），禁用验证和 hashtree 检查以允许本次 system 修改。这降低了启动完整性保护，仅用于已解锁并允许修改镜像启动的设备。使用本包期间不要重新锁定 BL。vbmeta_system、vbmeta_vendor、boot、recovery、lk 和 preloader 镜像均不写入。

二、包内文件

images/super.img                  去除管控实现后的 RAW super，3758096384 字节
images/vbmeta.img                 配套 flags=3 的 vbmeta，8388608 字节
images/MT6771_Android_scatter.txt  从原备份生成，仅启用 super、vbmeta
rollback/                        原始 super、vbmeta 及同样仅启用两分区的 scatter
tools/                           固定版本 MTKClient、CLI 依赖、布局检查和文件校验程序
tools/device_preloader.bin       原备份 preloader，仅供工具读取 DRAM 参数，不会被脚本刷入
sources/                         新桌面源码、签名密钥和本次构建/验证脚本
validation/                      改动清单、离线检查结果、工具来源与原文件 SHA256
SHA256SUMS.json                   静态包文件校验值

MTKClient 源码固定到官方提交：7cb40e727727dfe3faa065eefb29b16ed29bbdf1。
内含 V5 DA 已离线解析，包含 MT6771 的 DA 条目；这仍不等于已验证你平板的 DA 认证和 USB 通信。
本包 CLI 工具和所需 Python 模块已在工作目录配置并测试 --help 可运行。
PYTHON.cmd 优先使用这台电脑已有的 Codex Python；换电脑使用时需自行安装 64 位 Python 3.10 或更高版本并使 python 可用。

三、推荐刷入流程（MTK BROM/Preloader 端口）

0. 先将照片、文件、应用内资料单独备份。原 RAR 没有 userdata.img，无法用它恢复被清除的个人数据。将本包完整解压到短英文路径，例如 C:\C30_Clean；不要在压缩软件内直接运行。准备至少 20GB 可用空间供包和一次回读使用。重复读取时，旧文件会保留到 backup/history/ 或 readback/history/，需要额外空间。关闭其他占用 MTK 端口的工具。

1. 在包目录打开终端，执行：
      .\01_Verify_Files.cmd
   必须看到 PASS。若出现 STOP，停止，不写入。

2. 检查驱动及离线工具：
      .\MTK.cmd --help
   Windows 下 MTKClient 需要正常的 MTK 端口驱动及 UsbDk。本机 UsbDk 已安装，安装状态及重启要求见 tools/driver-status.txt，安装包也在 tools/。如果已能用原刷机工具连接，也可选择下面的 scatter 流程。

3. 平板关机、断开 USB。执行：
      .\02_Read_Layout.cmd
   然后按设备原来能进入 MTK 深刷端口的按键方法接线；常见为关机后按住音量键接线，具体以本机已验证的方法为准。工具识别后松开按键。
   此步骤读取 GPT 到 backup/gpt.bin，再验证 GPT CRC 和 8 个关键分区的起始地址/大小。必须看到 PASS。读取失败、DA/认证失败、端口不通或布局不符时停在这里；不要改为手填地址或整盘格式化。

4. 仍处于 MTK 连接状态，执行：
      .\03_Flash_Clean.cmd
   脚本先校验包和已读 GPT，再只写 super、vbmeta。不要选择 Format All、Firmware Upgrade 或刷入其他分区。工具若等待重新连接，重新关机接入同一台平板。

5. 写完后执行回读校验：
      .\04_Readback_Check.cmd
   会读取 super、vbmeta 到 readback/ 并逐个比较 SHA256。两个分区均须显示 PASS。失败时不要启动系统，检查连接并重新写入；不要用“工具返回成功”代替回读一致。

6. 回读通过后，清空旧签名记录、管控数据及加密元数据：
      .\05_Erase_User_Data.cmd
   此步骤明确清除 userdata、metadata、md_udc、cache。当前固件的 /metadata 实际挂载自 md_udc，所以必须一并处理。只运行一次即可；如报告任何格式化失败，先解决失败再启动。
   不清除 nvram、nvdata、nvcfg、persist、protect1、protect2、frp、seccfg，也不写 preloader/lk。

7. 执行：
      .\06_Reboot.cmd
   首次启动可能需要较长时间生成数据。进入后应看到“C30 桌面”。先验证设置、Wi-Fi、触摸、旋转、相机和应用启动，再安装其他软件。
   若出现验证红字、持续重启或长时间无法进入桌面，使用下面的回退流程；不要反复写 bootloader 或尝试重新锁定 BL。

四、使用原有支持 scatter 的 MTK 工具

如果原工具已经能对本机读写，可以加载 images/MT6771_Android_scatter.txt，并在界面核对实际只选中 super、vbmeta，使用逐分区 Download/Write 模式。此 scatter 保留原备份分区布局，未对所有 SP Flash Tool 版本做兼容测试；如解析失败，使用上面的 MTKClient 按 GPT 分区名写入流程。
刷后仍需回读比较 images/ 中两文件的 SHA256，并按第三节第 6 步清空四个数据分区，或用本机原厂 Recovery 正常执行恢复出厂设置。
不要加载原始 scatter 后全选；原 scatter 把许多分区以及缺失的 userdata.img 都标为可刷，这不适合本次操作。

五、回退

1. 重新进入相同 MTK 端口，保留 BL 解锁状态。
2. 执行 .\90_Restore_Original.cmd，只写 rollback/ 中原始 super、vbmeta。
3. 执行 .\91_Check_Original_Readback.cmd，要求两项 PASS。
4. 因新旧 APK 签名不同，再执行 .\05_Erase_User_Data.cmd，然后 .\06_Reboot.cmd。
5. 原管控会随原 super 恢复；个人数据在清除后不会恢复。若是端口/DA 连接失败，先恢复原来的驱动和连接方法，不要格式化整盘。

六、限制与来源

已验证的是离线结构、文件内容和工具加载；未验证真机启动和硬件功能。保留的框架接入点只会调用新的空接口，本次没有重建或替换 Android 框架，避免了与原预编译启动文件不匹配的改动。若厂商还有未暴露的专用校验，仍可能拒绝这个自签名桌面；当前不能排除这种硬件/固件特有行为。
本包不移除其他无证据表明属于皆成的系统组件。原厂 OTA 或重新刷入原始 super 可能恢复原管控。
生成的新桌面使用本地签名，证书与 Fundot 原证书不同，所以本次按清洁刷入设计。sources/launcher/c30-local.keystore 为本次生成的个人构建密钥，密码 c30-local-build，别名 c30，便于后续自行重建，不是厂商密钥。

官方资料：
MTKClient 使用说明：https://github.com/bkerler/mtkclient/blob/main/README-USAGE.md
MTKClient Windows 驱动要求：https://github.com/bkerler/mtkclient/blob/main/README-WINDOWS.md
UsbDk：https://github.com/daynix/UsbDk/releases
Android AVB：https://android.googlesource.com/platform/external/avb/
Android 动态分区：https://source.android.com/docs/core/ota/dynamic_partitions/implement
Google AAPT2：https://developer.android.com/tools/aapt2
