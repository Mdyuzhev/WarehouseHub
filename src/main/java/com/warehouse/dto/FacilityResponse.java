package com.warehouse.dto;

import com.warehouse.model.Facility;
import com.warehouse.model.FacilityType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * DTO для ответа с информацией об объекте
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FacilityResponse {

    private Long id;
    private String code;
    private FacilityType type;
    private String name;
    private Long parentId;
    private String address;
    private String status;
    private LocalDateTime createdAt;

    public static FacilityResponse from(Facility facility) {
        return FacilityResponse.builder()
                .id(facility.getId())
                .code(facility.getCode())
                .type(facility.getType())
                .name(facility.getName())
                .parentId(facility.getParentId())
                .address(facility.getAddress())
                .status(facility.getStatus())
                .createdAt(facility.getCreatedAt())
                .build();
    }
}
