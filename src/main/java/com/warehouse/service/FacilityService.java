package com.warehouse.service;

import com.warehouse.dto.FacilityCreateRequest;
import com.warehouse.dto.FacilityResponse;
import com.warehouse.dto.FacilityTreeNode;
import com.warehouse.dto.FacilityUpdateRequest;
import com.warehouse.model.Facility;
import com.warehouse.model.FacilityType;
import com.warehouse.repository.FacilityRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Сервис для работы с объектами логистической сети
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class FacilityService {

    private final FacilityRepository facilityRepository;

    /**
     * Получить все объекты
     */
    @Transactional(readOnly = true)
    public List<FacilityResponse> findAll() {
        return facilityRepository.findAll().stream()
                .map(FacilityResponse::from)
                .collect(Collectors.toList());
    }

    /**
     * Получить объект по ID
     */
    @Transactional(readOnly = true)
    public FacilityResponse findById(Long id) {
        Facility facility = facilityRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Facility not found with id: " + id));
        return FacilityResponse.from(facility);
    }

    /**
     * Получить объект по коду
     */
    @Transactional(readOnly = true)
    public FacilityResponse findByCode(String code) {
        Facility facility = facilityRepository.findByCode(code)
                .orElseThrow(() -> new IllegalArgumentException("Facility not found with code: " + code));
        return FacilityResponse.from(facility);
    }

    /**
     * Получить объекты по типу
     */
    @Transactional(readOnly = true)
    public List<FacilityResponse> findByType(FacilityType type) {
        return facilityRepository.findByType(type).stream()
                .map(FacilityResponse::from)
                .collect(Collectors.toList());
    }

    /**
     * Получить дочерние объекты
     */
    @Transactional(readOnly = true)
    public List<FacilityResponse> findChildren(Long parentId) {
        return facilityRepository.findByParentId(parentId).stream()
                .map(FacilityResponse::from)
                .collect(Collectors.toList());
    }

    /**
     * Получить иерархию объектов в виде дерева
     * Структура: DC → WH → PP
     */
    @Transactional(readOnly = true)
    public List<FacilityTreeNode> getTree() {
        List<Facility> allDCs = facilityRepository.findAllDistributionCenters();
        List<FacilityTreeNode> tree = new ArrayList<>();

        for (Facility dc : allDCs) {
            FacilityTreeNode dcNode = FacilityTreeNode.from(dc);

            // Получить склады для этого РЦ
            List<Facility> warehouses = facilityRepository.findWarehousesByDcId(dc.getId());
            for (Facility wh : warehouses) {
                FacilityTreeNode whNode = FacilityTreeNode.from(wh);

                // Получить пункты выдачи для этого склада
                List<Facility> pickupPoints = facilityRepository.findPickupPointsByWarehouseId(wh.getId());
                for (Facility pp : pickupPoints) {
                    whNode.addChild(FacilityTreeNode.from(pp));
                }

                dcNode.addChild(whNode);
            }

            tree.add(dcNode);
        }

        return tree;
    }

    /**
     * Создать новый объект с автогенерацией кода
     */
    @Transactional
    public FacilityResponse create(FacilityCreateRequest request) {
        log.info("Creating new facility: type={}, name={}", request.getType(), request.getName());

        // Валидация иерархии
        validateHierarchy(request.getType(), request.getParentId());

        // Автогенерация кода
        String code = generateCode(request.getType(), request.getRegion(), request.getParentId());
        log.info("Generated code: {}", code);

        // Проверка уникальности кода
        if (facilityRepository.existsByCode(code)) {
            throw new IllegalArgumentException("Facility with code " + code + " already exists");
        }

        Facility facility = Facility.builder()
                .code(code)
                .type(request.getType())
                .name(request.getName())
                .parentId(request.getParentId())
                .address(request.getAddress())
                .build();

        Facility saved = facilityRepository.save(facility);
        log.info("Facility created successfully: id={}, code={}", saved.getId(), saved.getCode());

        return FacilityResponse.from(saved);
    }

    /**
     * Обновить объект
     */
    @Transactional
    public FacilityResponse update(Long id, FacilityUpdateRequest request) {
        log.info("Updating facility: id={}", id);

        Facility facility = facilityRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Facility not found with id: " + id));

        if (request.getName() != null) {
            facility.setName(request.getName());
        }
        if (request.getAddress() != null) {
            facility.setAddress(request.getAddress());
        }
        if (request.getStatus() != null) {
            facility.setStatus(request.getStatus());
        }

        Facility updated = facilityRepository.save(facility);
        log.info("Facility updated successfully: id={}", updated.getId());

        return FacilityResponse.from(updated);
    }

    /**
     * Валидация иерархии объектов
     * - DC: parentId должен быть null
     * - WH: parentId должен указывать на существующий DC
     * - PP: parentId должен указывать на существующий WH
     */
    public void validateHierarchy(FacilityType type, Long parentId) {
        switch (type) {
            case DC:
                if (parentId != null) {
                    throw new IllegalArgumentException("Distribution Center (DC) cannot have a parent");
                }
                break;
            case WH:
                if (parentId == null) {
                    throw new IllegalArgumentException("Warehouse (WH) must have a parent Distribution Center");
                }
                Facility dcParent = facilityRepository.findById(parentId)
                        .orElseThrow(() -> new IllegalArgumentException("Parent DC not found with id: " + parentId));
                if (dcParent.getType() != FacilityType.DC) {
                    throw new IllegalArgumentException("Warehouse parent must be a Distribution Center (DC)");
                }
                break;
            case PP:
                if (parentId == null) {
                    throw new IllegalArgumentException("Pickup Point (PP) must have a parent Warehouse");
                }
                Facility whParent = facilityRepository.findById(parentId)
                        .orElseThrow(() -> new IllegalArgumentException("Parent WH not found with id: " + parentId));
                if (whParent.getType() != FacilityType.WH) {
                    throw new IllegalArgumentException("Pickup Point parent must be a Warehouse (WH)");
                }
                break;
        }
    }

    /**
     * Автогенерация кода объекта
     * - DC: DC-001, DC-002, ...
     * - WH: WH-{region}-001, WH-{region}-002, ... (например, WH-C-001, WH-N-002)
     * - PP: PP-{region}-{wh_number}-01, PP-{region}-{wh_number}-02, ... (например, PP-C-001-01, PP-N-002-03)
     */
    public String generateCode(FacilityType type, String region, Long parentId) {
        switch (type) {
            case DC:
                Integer maxDcNumber = facilityRepository.findMaxDcNumber();
                int nextDcNumber = (maxDcNumber == null) ? 1 : maxDcNumber + 1;
                return String.format("DC-%03d", nextDcNumber);

            case WH:
                if (region == null || region.isEmpty()) {
                    throw new IllegalArgumentException("Region is required for Warehouse code generation");
                }
                String whPrefix = "WH-" + region.toUpperCase() + "-";
                Integer maxWhNumber = facilityRepository.findMaxWhNumberByRegion(whPrefix);
                int nextWhNumber = (maxWhNumber == null) ? 1 : maxWhNumber + 1;
                return String.format("%s%03d", whPrefix, nextWhNumber);

            case PP:
                if (parentId == null) {
                    throw new IllegalArgumentException("Parent warehouse is required for Pickup Point code generation");
                }
                Facility warehouse = facilityRepository.findById(parentId)
                        .orElseThrow(() -> new IllegalArgumentException("Parent warehouse not found"));

                // Извлечь регион и номер склада из кода WH (например, WH-C-001)
                String whCode = warehouse.getCode();
                String ppPrefix = whCode.replace("WH-", "PP-") + "-";

                Integer maxPpNumber = facilityRepository.findMaxPpNumberByWarehouse(ppPrefix);
                int nextPpNumber = (maxPpNumber == null) ? 1 : maxPpNumber + 1;
                return String.format("%s%02d", ppPrefix, nextPpNumber);

            default:
                throw new IllegalArgumentException("Unknown facility type: " + type);
        }
    }
}
