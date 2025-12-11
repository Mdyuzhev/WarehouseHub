package com.warehouse.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Акт выдачи товара клиенту
 * WH-275: Issue Acts
 *
 * State Machine: DRAFT → COMPLETED
 * - COMPLETED: instant stock deduction (no reservation)
 * - Only for PP (pickup points)
 */
@Entity
@Table(name = "issue_acts")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IssueAct {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Номер документа
     * Формат: ISS-{facilityCode}-{YYYYMMDD}-{seq}
     * Пример: ISS-PP-M-001-20251211-001
     */
    @Column(name = "document_number", unique = true, nullable = false, length = 50)
    private String documentNumber;

    /**
     * ПВЗ (только pickup points!)
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "facility_id", nullable = false)
    private Facility facility;

    /**
     * Имя клиента
     */
    @Column(name = "customer_name", nullable = false)
    private String customerName;

    /**
     * Телефон клиента
     */
    @Column(name = "customer_phone", length = 50)
    private String customerPhone;

    /**
     * Статус документа
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private IssueStatus status = IssueStatus.DRAFT;

    /**
     * Примечания
     */
    @Column(columnDefinition = "TEXT")
    private String notes;

    /**
     * Создан пользователем
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by")
    private User createdBy;

    /**
     * Дата создания
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Дата завершения (товар выдан)
     */
    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    /**
     * Позиции документа
     */
    @OneToMany(mappedBy = "issueAct", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @Builder.Default
    private List<IssueActItem> items = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }

    /**
     * Добавить позицию
     */
    public void addItem(IssueActItem item) {
        items.add(item);
        item.setIssueAct(this);
    }

    /**
     * Удалить позицию
     */
    public void removeItem(IssueActItem item) {
        items.remove(item);
        item.setIssueAct(null);
    }
}
