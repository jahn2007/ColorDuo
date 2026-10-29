/* SPDX-License-Identifier: GPL-3.0-only */
package io.github.yixing233.hyperduo;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.UserManager;

/** One persistent store shared by UI and the read-only SystemUI provider. */
public final class LegacySettings {
    public static final String AUTHORITY = "io.github.chorusfruit_233.colorduo.legacy.settings";
    private static final String META = "legacy_transport";
    private LegacySettings() {}

    public static synchronized SharedPreferences preferences(Context context) {
        Context device = context.createDeviceProtectedStorageContext();
        SharedPreferences metadata = device.getSharedPreferences(META, Context.MODE_PRIVATE);
        UserManager users = context.getSystemService(UserManager.class);
        if (!metadata.getBoolean("migrated", false) && users != null && users.isUserUnlocked()) {
            // The modern settings UI already saved a local mirror; retain all styles and keys.
            SharedPreferences.Editor target = device.getSharedPreferences(Prefs.NAME, Context.MODE_PRIVATE).edit();
            for (java.util.Map.Entry<String, ?> entry : context.getSharedPreferences(Prefs.NAME, Context.MODE_PRIVATE).getAll().entrySet()) {
                String key = entry.getKey(); Object value = entry.getValue();
                if (value instanceof Boolean) target.putBoolean(key, (Boolean) value);
                else if (value instanceof Integer) target.putInt(key, (Integer) value);
                else if (value instanceof Long) target.putLong(key, (Long) value);
                else if (value instanceof Float) target.putFloat(key, (Float) value);
                else if (value instanceof String) target.putString(key, (String) value);
                else if (value instanceof java.util.Set) {
                    @SuppressWarnings("unchecked") java.util.Set<String> strings = (java.util.Set<String>) value;
                    target.putStringSet(key, new java.util.HashSet<>(strings));
                }
            }
            if (target.commit()) metadata.edit().putBoolean("migrated", true).commit();
        }
        return device.getSharedPreferences(Prefs.NAME, Context.MODE_PRIVATE);
    }

    static void heartbeat(Context context, int api) {
        context.createDeviceProtectedStorageContext().getSharedPreferences(META, Context.MODE_PRIVATE)
                .edit().putLong("seen", System.currentTimeMillis()).putInt("api", api).apply();
    }

    public static Bundle status(Context context) {
        SharedPreferences p = context.createDeviceProtectedStorageContext().getSharedPreferences(META, Context.MODE_PRIVATE);
        long age = System.currentTimeMillis() - p.getLong("seen", 0);
        Bundle result = new Bundle();
        result.putBoolean("active", age >= 0 && age < 20_000);
        result.putInt("api", p.getInt("api", 0));
        return result;
    }
}
