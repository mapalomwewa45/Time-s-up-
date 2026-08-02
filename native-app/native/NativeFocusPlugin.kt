package com.timesup.app.focus

import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Process
import android.provider.Settings
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

/**
 * Bridges window.NativeFocus.start()/stop() from the web app to Android.
 * Register this in MainActivity with: registerPlugin(NativeFocusPlugin::class.java)
 */
@CapacitorPlugin(name = "NativeFocus")
class NativeFocusPlugin : Plugin() {

    @PluginMethod
    fun start(call: PluginCall) {
        val appsArray = call.getArray("apps")
        val apps = mutableListOf<String>()
        if (appsArray != null) {
            for (i in 0 until appsArray.length()) {
                apps.add(appsArray.getString(i))
            }
        }
        val minutes = call.getInt("minutes") ?: 25

        if (!hasUsageAccess()) {
            requestUsageAccess()
            call.reject("Usage access isn't granted yet. Opened Settings — ask the user to enable it for Time's Up, then try again.")
            return
        }

        val endAt = System.currentTimeMillis() + minutes * 60_000L
        FocusBlockerService.start(context, apps, endAt)

        val ret = JSObject()
        ret.put("started", true)
        ret.put("endAt", endAt)
        call.resolve(ret)
    }

    @PluginMethod
    fun stop(call: PluginCall) {
        FocusBlockerService.stop(context)
        val ret = JSObject()
        ret.put("stopped", true)
        call.resolve(ret)
    }

    private fun hasUsageAccess(): Boolean {
        val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            appOps.unsafeCheckOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName)
        } else {
            @Suppress("DEPRECATION")
            appOps.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName)
        }
        return mode == AppOpsManager.MODE_ALLOWED
    }

    private fun requestUsageAccess() {
        val intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    }
}
