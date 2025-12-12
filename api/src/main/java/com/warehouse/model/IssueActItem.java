package com.warehouse.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Позиция акта выдачи
 * WH-275: Issue Acts
 */
@Entity
@Table(name = "issue_act_items")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IssueActItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Акт выдачи
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "issue_act_id", nullable = false)
    private IssueAct issueAct;

    /**
     * Товар
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    private Product product;

    /**
     * Количество к выдаче
     */
    @Column(nullable = false)
    private Integer quantity;
}
