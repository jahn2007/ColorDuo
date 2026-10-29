/* SPDX-License-Identifier: GPL-3.0-only */
package io.github.yixing233.hyperduo;
final class LegacyLogger {
    void log(int priority, String tag, String message) {
        de.robv.android.xposed.XposedBridge.log(tag + ": " + message);
    }
}
