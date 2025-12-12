package com.warehouse.dto;

import com.warehouse.model.Facility;
import com.warehouse.model.FacilityType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

/**
 * DTO для представления иерархии объектов в виде дерева
 * Структура: DC → [WH] → [PP]
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class FacilityTreeNode {

    private Long id;
    private String code;
    private FacilityType type;
    private String name;
    private String address;
    private String status;

    @Builder.Default
    private List<FacilityTreeNode> children = new ArrayList<>();

    public static FacilityTreeNode from(Facility facility) {
        return FacilityTreeNode.builder()
                .id(facility.getId())
                .code(facility.getCode())
                .type(facility.getType())
                .name(facility.getName())
                .address(facility.getAddress())
                .status(facility.getStatus())
                .children(new ArrayList<>())
                .build();
    }

    public void addChild(FacilityTreeNode child) {
        this.children.add(child);
    }
}
