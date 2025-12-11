package com.warehouse.model;

/**
 * Статус акта выдачи
 * WH-275: Issue Acts
 *
 * Простой flow: DRAFT → COMPLETED
 */
public enum IssueStatus {
    /**
     * Черновик
     */
    DRAFT,

    /**
     * Выдано клиенту (товар списан со склада)
     */
    COMPLETED
}
