package com.timesup.app.focus

import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Full-screen lock screen launched on top of any blocked app while Focus Mode is active.
 * Tapping the button sends the user back into Time's Up instead of the blocked app.
 */
class BlockerOverlayActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.parseColor("#0F172A"))
            setPadding(60, 60, 60, 60)
        }
        val title = TextView(this).apply {
            text = "Focus Mode is on"
            textSize = 22f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
        }
        val subtitle = TextView(this).apply {
            text = "This app is blocked until your Time's Up session ends."
            textSize = 15f
            setTextColor(Color.parseColor("#C9A34E"))
            gravity = Gravity.CENTER
            setPadding(0, 24, 0, 40)
        }
        val backBtn = Button(this).apply {
            text = "Back to Time's Up"
            setOnClickListener {
                val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
                launchIntent?.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                startActivity(launchIntent)
                finish()
            }
        }
        layout.addView(title)
        layout.addView(subtitle)
        layout.addView(backBtn)
        setContentView(layout)
    }

    companion object {
        fun launch(context: Context) {
            val intent = Intent(context, BlockerOverlayActivity::class.java)
            intent.addFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK or
                Intent.FLAG_ACTIVITY_CLEAR_TOP or
                Intent.FLAG_ACTIVITY_SINGLE_TOP
            )
            context.startActivity(intent)
        }
    }
}
