package com.warehouse.dto;

import com.warehouse.model.FacilityType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO для создания нового объекта логистической сети
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FacilityCreateRequest {

    @NotNull(message = "Type is required")
    private FacilityType type;

    @NotBlank(message = "Name is required")
    private String name;

    /**
     * ID родительского объекта
     * - null для DC (корневой уровень)
     * - ID распределительного центра для WH
     * - ID склада для PP
     */
    private Long parentId;

    private String address;

    /**
     * Регион для автогенерации кода WH и PP
     * Примеры: "C" (Central), "N" (North), "S" (South), "E" (East), "W" (West)
     * Используется только для WH и PP
     */
    private String region;
}
