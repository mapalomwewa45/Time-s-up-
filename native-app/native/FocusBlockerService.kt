package com.timesup.app.focus

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.core.app.NotificationCompat

/**
 * Polls the foreground app once a second using UsageStatsManager and shows
 * BlockerOverlayActivity on top whenever a blocked package is detected.
 * Runs as a foreground service so Android doesn't kill it mid-session.
 */
class FocusBlockerService : Service() {

    private val handler = Handler(Looper.getMainLooper())
    private var blockedApps: List<String> = emptyList()
    private var endAt: Long = 0L
    private var running = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        blockedApps = intent?.getStringArrayListExtra(EXTRA_APPS) ?: arrayListOf()
        endAt = intent?.getLongExtra(EXTRA_END_AT, 0L) ?: 0L
        startForeground(NOTIF_ID, buildNotification())
        running = true
        pollLoop()
        return START_STICKY
    }

    private fun pollLoop() {
        if (!running) return
        if (System.currentTimeMillis() >= endAt) {
            stopSelf()
            return
        }
        val foreground = getForegroundApp()
        if (foreground != null && blockedApps.contains(foreground)) {
            BlockerOverlayActivity.launch(this)
        }
        handler.postDelayed({ pollLoop() }, 1000)
    }

    private fun getForegroundApp(): String? {
        val usm = getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
        val end = System.currentTimeMillis()
        val begin = end - 10_000
        val events = usm.queryEvents(begin, end)
        var lastApp: String? = null
        val event = UsageEvents.Event()
        while (events.hasNextEvent()) {
            events.getNextEvent(event)
            if (event.eventType == UsageEvents.Event.MOVE_TO_FOREGROUND) {
                lastApp = event.packageName
            }
        }
        return lastApp
    }

    private fun buildNotification(): Notification {
        val channelId = "focus_mode"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(channelId, "Focus Mode", NotificationManager.IMPORTANCE_LOW)
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(channel)
        }
        return NotificationCompat.Builder(this, channelId)
            .setContentTitle("Time's Up — Focus Mode")
            .setContentText("Distracting apps are blocked until your session ends.")
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setOngoing(true)
            .build()
    }

    override fun onDestroy() {
        running = false
        super.onDestroy()
    }

    companion object {
        const val EXTRA_APPS = "apps"
        const val EXTRA_END_AT = "endAt"
        private const val NOTIF_ID = 4471

        fun start(context: Context, apps: List<String>, endAt: Long) {
            val intent = Intent(context, FocusBlockerService::class.java)
            intent.putStringArrayListExtra(EXTRA_APPS, ArrayList(apps))
            intent.putExtra(EXTRA_END_AT, endAt)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, FocusBlockerService::class.java))
        }
    }
}
