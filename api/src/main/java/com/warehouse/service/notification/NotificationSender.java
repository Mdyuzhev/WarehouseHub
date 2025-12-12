package com.warehouse.service.notification;

import com.warehouse.model.Notification;
import com.warehouse.model.NotificationChannel;

/**
 * Интерфейс для отправки уведомлений через различные каналы
 */
public interface NotificationSender {

    /**
     * Отправить уведомление
     *
     * @param notification уведомление для отправки
     * @return true если отправка успешна, false в случае ошибки
     */
    boolean send(Notification notification);

    /**
     * Проверяет, поддерживает ли sender данный канал
     *
     * @param channel канал отправки
     * @return true если канал поддерживается
     */
    boolean supports(NotificationChannel channel);

    /**
     * Получить имя канала
     *
     * @return название канала для логирования
     */
    String getChannelName();
}
