/* SPDX-License-Identifier: GPL-3.0-only */
package io.github.yixing233.hyperduo;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import java.lang.reflect.Executable;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;

/** Real before/after callbacks: preserve the native call and other modules' hook chain. */
final class LegacyHook {
    interface Action { void run(XC_MethodHook.MethodHookParam param) throws Throwable; }
    interface Step { void run(Frame frame) throws Throwable; }
    static final class Frame {
        final XC_MethodHook.MethodHookParam param;
        Object data;
        boolean outer;
        Frame(XC_MethodHook.MethodHookParam param) { this.param = param; }
    }
    private static final AtomicInteger IDS = new AtomicInteger();
    private static final Set<Executable> INSTALLED = new HashSet<>();

    static int after(Executable method, Action callback) {
        return around(method, frame -> {}, frame -> {
            if (!frame.param.hasThrowable()) callback.run(frame.param);
        });
    }

    static synchronized int around(Executable method, Step before, Step after) {
        if (method == null || INSTALLED.contains(method)) return 0;
        String key = "ColorDuo.legacy.frame." + IDS.incrementAndGet();
        try {
            method.setAccessible(true);
            XposedBridge.hookMethod(method, new XC_MethodHook() {
                @Override protected void beforeHookedMethod(MethodHookParam param) {
                    Frame frame = new Frame(param);
                    param.setObjectExtra(key, frame);
                    try { before.run(frame); }
                    catch (Throwable error) { XposedBridge.log(error); }
                }
                @Override protected void afterHookedMethod(MethodHookParam param) {
                    Frame frame = (Frame) param.getObjectExtra(key);
                    if (frame == null) return;
                    try { after.run(frame); }
                    catch (Throwable error) { XposedBridge.log(error); }
                    finally { param.setObjectExtra(key, null); }
                }
            });
            INSTALLED.add(method);
            return 1;
        } catch (Throwable error) {
            XposedBridge.log(error);
            return 0;
        }
    }
}
