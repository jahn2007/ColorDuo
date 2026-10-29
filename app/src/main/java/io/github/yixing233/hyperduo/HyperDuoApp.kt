/* SPDX-License-Identifier: GPL-3.0-only */
package io.github.yixing233.hyperduo

import android.app.Application
import android.os.Handler
import android.os.Looper
import java.util.concurrent.CopyOnWriteArraySet

/** Actual SystemUI heartbeat, independent of modern framework services. */
data class LegacyFrameworkInfo(val apiVersion: Int) {
    val frameworkName = "Xposed-compatible"
    val frameworkVersion = "Legacy"
    val frameworkVersionCode = apiVersion.toLong()
    val scope = listOf(Prefs.SYSTEMUI_PACKAGE)
}

class HyperDuoApp : Application() {
    override fun onCreate() {
        super.onCreate()
        LegacySettings.preferences(this)
        val main = Handler(Looper.getMainLooper())
        main.post(object : Runnable {
            override fun run() {
                val status = LegacySettings.status(this@HyperDuoApp)
                val next = if (status.getBoolean("active")) LegacyFrameworkInfo(status.getInt("api")) else null
                if (next != legacyStatus) {
                    legacyStatus = next
                    listeners.forEach { it(next) }
                }
                main.postDelayed(this, 2000L)
            }
        })
    }
    companion object {
        @Volatile var legacyStatus: LegacyFrameworkInfo? = null
            private set
        private val listeners = CopyOnWriteArraySet<(LegacyFrameworkInfo?) -> Unit>()
        fun addStatusListener(listener: (LegacyFrameworkInfo?) -> Unit) {
            listeners.add(listener)
            listener(legacyStatus)
        }
        fun removeStatusListener(listener: (LegacyFrameworkInfo?) -> Unit) { listeners.remove(listener) }
    }
}
