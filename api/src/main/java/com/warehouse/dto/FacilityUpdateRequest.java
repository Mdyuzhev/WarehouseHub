package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO для обновления объекта логистической сети
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FacilityUpdateRequest {

    private String name;

    private String address;

    /**
     * Статус: ACTIVE, INACTIVE, CLOSED
     */
    private String status;
}
