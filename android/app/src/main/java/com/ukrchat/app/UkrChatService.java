package com.ukrchat.app;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

public class UkrChatService extends Service {

    @Override
    public void onCreate() {
        super.onCreate();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Тут буде запуск локального llama.cpp
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        // Тут буде зупинка локального AI-сервера
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
