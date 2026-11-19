# C30 Clean MTK 测试包

**本仓库不提交或上传 super.img；镜像是刷机时由使用者在本地准备的输入。** 针对说明中的原备份和硬件布局，把修改后的 RAW 镜像放到 `images/super.img`，把原始回退镜像放到 `rollback/super.img`，校验通过后再执行刷写。脚本会将修改后的整个 super 分区镜像写入设备，不会在设备上自动修改原镜像。

构建、测试、连接保护与完整发行包要求见 [BUILD_AND_RELEASE.md](docs/BUILD_AND_RELEASE.md)。桌面源码的新改动尚未重建到历史 APK/固件中。

刷机步骤与使用说明见 [README_刷机步骤.txt](README_刷机步骤.txt)。

## 开源许可证

本仓库原创代码采用 **GNU GPL v3.0（GPL-3.0-only）**，完整条款见 [LICENSE](LICENSE)。

授权范围为仓库根目录的原创 `.cmd` 脚本、`sources/` 中的原创 Python 和 Java 源码及 `AndroidManifest.xml`，以及 `tools/` 根目录的原创 Python 辅助脚本、`tests/` 中的原创测试代码和 `.github/workflows/` 工作流配置：

- `tools/check_layout.py`
- `tools/prepare_read.py`
- `tools/run_mtk.py`
- `tools/verify_files.py`

你可以按 GPL-3.0 使用、修改和分发这些代码，包括商业使用。分发修改版或基于这些代码的衍生程序时，应遵守 GPL 对许可证、声明和相应源码提供等方面的要求。软件按许可证条款提供，不作担保。

## 第三方内容及授权范围

上述授权仅适用于仓库贡献者有权授权的原创代码，不覆盖整个文件夹中的所有文件。

- `tools/mtkclient/` 保留其自身的 [GPL-3.0 许可证](tools/mtkclient/LICENSE)及原有版权声明。
- `tools/python-packages/` 中的依赖保留各自的许可证及版权声明。
- 第三方安装包、驱动、加载器、预加载器、固件及镜像（包括 `images/`、`rollback/`、`tools/device_preloader.bin` 和 `tools/UsbDk_1.0.22_x64.msi`）不因本仓库公开或添加 GPL 而获得新的开源授权；使用、修改和再分发仍须遵守各自适用的授权。
- 其他二进制文件、签名密钥、验证记录和文档不在上述源码许可范围内。本声明不授予第三方商标或其他权利。
