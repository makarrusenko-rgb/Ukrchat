package com.ukrchat.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;

public class UkrChatService extends Service {

    private static final String CHANNEL_ID = "ukrchat_ai";
    private static final int NOTIFICATION_ID = 1;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {

        Notification notification = new Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("УкрЧат")
                .setContentText("Локальний AI працює")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setOngoing(true)
                .build();

        startForeground(NOTIFICATION_ID, notification);

        // Пізніше тут буде запуск llama.cpp.

        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();

        // Пізніше тут буде зупинка llama.cpp.
    }

    private void createNotificationChannel() {

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {

            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "УкрЧат AI",
                    NotificationManager.IMPORTANCE_LOW
            );

            channel.setDescription(
                    "Стан локального AI-сервера УкрЧату"
            );

            NotificationManager manager =
                    getSystemService(NotificationManager.class);

            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
