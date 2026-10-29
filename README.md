# ColorDuo Legacy

`legacy` 分支使用传统 Xposed API（最低 API 82），作用域为系统界面 `com.android.systemui`。

- 保留 Wi-Fi / 网络类型优先级修复、双卡信号、充电功率及暂停充电灰度范围设置。
- 使用标准 before/after Hook；不依赖 libxposed API 或服务。
- 设置保存在设备保护存储，通过仅允许 SystemUI 读取的 ContentProvider 同步。广播只通知重新读取，设置实时生效；丢失通知时每 5 秒重试。
- 首次运行复制原应用本地配置，保留各样式配置；不删除现代版原有本地配置文件。
- APK 更新后重启 SystemUI 或手机，不支持现代 API 102 的 APK 热重载。

## 构建

推送到 `legacy` 或手动运行 **Build Legacy APK**。工作流先执行回归检查，再使用 JDK 21、Android SDK 37、Build Tools 37.0.0 构建开发签名 Debug APK，校验签名、版本和 legacy 模块入口并上传 APK、SHA256SUMS 和 build-info.json。

开发签名与本 fork 的现代测试版一致，可覆盖安装；与上游正式签名不同。切换版本后需重启 SystemUI。legacy 版需要单独真机验证。

基于 [ColorDuo](https://github.com/chorusfruit-233/ColorDuo) / [HyperDuo](https://github.com/yixing233/HyperDuo)，遵循 GPL-3.0-only。
