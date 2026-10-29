/* SPDX-License-Identifier: GPL-3.0-only */
package io.github.yixing233.hyperduo;

import android.app.Application;
import android.content.Context;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

/** Legacy Xposed entry. No libxposed API or APK hot-reload lifecycle is used. */
public final class HyperDuoModule implements IXposedHookLoadPackage {
    private static boolean installed;
    @Override public void handleLoadPackage(XC_LoadPackage.LoadPackageParam param) {
        if (!Prefs.SYSTEMUI_PACKAGE.equals(param.packageName)
                || !Prefs.SYSTEMUI_PACKAGE.equals(param.processName)) return;
        // Application.attach uses the target's final application classloader, after factory setup.
        LegacyHook.after(Refl.method(Application.class, "attach", Context.class), hook -> {
            synchronized (HyperDuoModule.class) {
                if (installed) return;
                Context context = (Context) hook.args[0];
                ClassLoader loader = context.getClassLoader();
                if (Refl.cls(ColorOsHooks.METER_CLASS, loader) == null) {
                    XposedBridge.log("ColorDuo Legacy: unsupported ColorOS battery classes");
                    return;
                }
                installed = true;
                try {
                    ColorOsHooks.install(loader);
                    TrioConfig.installReceiver(context);
                    XposedBridge.log("ColorDuo Legacy: SystemUI hooks installed");
                } catch (Throwable error) { XposedBridge.log(error); }
            }
        });
    }
}
