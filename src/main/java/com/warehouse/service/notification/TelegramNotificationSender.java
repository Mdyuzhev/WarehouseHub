package com.warehouse.service.notification;

import com.warehouse.model.Notification;
import com.warehouse.model.NotificationChannel;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * Telegram реализация NotificationSender
 * Отправляет уведомления через Telegram Bot API
 */
@Component
@Slf4j
public class TelegramNotificationSender implements NotificationSender {

    @Value("${notification.telegram.bot-token}")
    private String botToken;

    @Value("${notification.telegram.default-chat-id}")
    private String defaultChatId;

    private final RestTemplate restTemplate = new RestTemplate();

    @Override
    public boolean supports(NotificationChannel channel) {
        return channel == NotificationChannel.TELEGRAM;
    }

    @Override
    public String getChannelName() {
        return "Telegram";
    }

    @Override
    public boolean send(Notification notification) {
        String url = String.format("https://api.telegram.org/bot%s/sendMessage", botToken);
        String chatId = notification.getRecipient() != null
            ? notification.getRecipient()
            : defaultChatId;

        Map<String, Object> body = new HashMap<>();
        body.put("chat_id", chatId);
        body.put("text", formatMessage(notification));
        body.put("parse_mode", "HTML");

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(url, body, String.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.error("Telegram send failed: {}", e.getMessage());
            return false;
        }
    }

    private String formatMessage(Notification notification) {
        if (notification.getSubject() != null) {
            return String.format("<b>%s</b>\n\n%s", notification.getSubject(), notification.getMessage());
        }
        return notification.getMessage();
    }
}
