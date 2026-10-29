/* SPDX-License-Identifier: GPL-3.0-only */
package io.github.yixing233.hyperduo;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.Binder;
import android.os.Bundle;
import android.os.Process;

/** Only the settings app and SystemUI may read the complete configuration. No remote writes. */
public final class LegacySettingsProvider extends ContentProvider {
    @Override public boolean onCreate() { return true; }
    private void enforceCaller() {
        int uid = Binder.getCallingUid();
        if (uid == Process.myUid()) return;
        String[] packages = getContext().getPackageManager().getPackagesForUid(uid);
        if (packages != null) for (String name : packages) {
            if (Prefs.SYSTEMUI_PACKAGE.equals(name)) return;
        }
        throw new SecurityException("ColorDuo settings are restricted to SystemUI");
    }
    @Override public Bundle call(String method, String arg, Bundle extras) {
        enforceCaller();
        if (!"snapshot".equals(method)) throw new IllegalArgumentException("Unknown method");
        LegacySettings.heartbeat(getContext(), extras == null ? 0 : extras.getInt("api", 0));
        return TrioSettings.from(LegacySettings.preferences(getContext()),
                getContext().getResources().getDisplayMetrics().density).toBundle();
    }
    @Override public Cursor query(Uri u, String[] p, String s, String[] a, String order) { throw new UnsupportedOperationException(); }
    @Override public String getType(Uri u) { return null; }
    @Override public Uri insert(Uri u, ContentValues v) { throw new UnsupportedOperationException(); }
    @Override public int update(Uri u, ContentValues v, String s, String[] a) { throw new UnsupportedOperationException(); }
    @Override public int delete(Uri u, String s, String[] a) { throw new UnsupportedOperationException(); }
}
