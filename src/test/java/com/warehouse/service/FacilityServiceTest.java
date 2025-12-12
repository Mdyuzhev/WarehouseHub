package com.warehouse.service;

import com.warehouse.dto.FacilityCreateRequest;
import com.warehouse.dto.FacilityResponse;
import com.warehouse.model.Facility;
import com.warehouse.model.FacilityType;
import com.warehouse.repository.FacilityRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("FacilityService Tests")
class FacilityServiceTest {

    @Mock
    private FacilityRepository facilityRepository;

    @InjectMocks
    private FacilityService facilityService;

    private Facility dcFacility;
    private Facility whFacility;
    private Facility ppFacility;

    @BeforeEach
    void setUp() {
        dcFacility = Facility.builder()
                .id(1L)
                .code("DC-001")
                .type(FacilityType.DC)
                .name("Distribution Center 1")
                .parentId(null)
                .address("123 Main St")
                .status("ACTIVE")
                .createdAt(LocalDateTime.now())
                .build();

        whFacility = Facility.builder()
                .id(2L)
                .code("WH-C-001")
                .type(FacilityType.WH)
                .name("Central Warehouse 1")
                .parentId(1L)
                .address("456 Storage Ave")
                .status("ACTIVE")
                .createdAt(LocalDateTime.now())
                .build();

        ppFacility = Facility.builder()
                .id(3L)
                .code("PP-C-001-01")
                .type(FacilityType.PP)
                .name("Pickup Point 1")
                .parentId(2L)
                .address("789 Delivery Rd")
                .status("ACTIVE")
                .createdAt(LocalDateTime.now())
                .build();
    }

    @Test
    @DisplayName("Should find facility by code successfully")
    void testFindByCode_Success() {
        // Given
        when(facilityRepository.findByCode("DC-001")).thenReturn(Optional.of(dcFacility));

        // When
        FacilityResponse result = facilityService.findByCode("DC-001");

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getCode()).isEqualTo("DC-001");
        assertThat(result.getType()).isEqualTo(FacilityType.DC);
        verify(facilityRepository).findByCode("DC-001");
    }

    @Test
    @DisplayName("Should throw exception when facility not found by code")
    void testFindByCode_NotFound() {
        // Given
        when(facilityRepository.findByCode("DC-999")).thenReturn(Optional.empty());

        // When/Then
        assertThatThrownBy(() -> facilityService.findByCode("DC-999"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Facility not found with code: DC-999");

        verify(facilityRepository).findByCode("DC-999");
    }

    @Test
    @DisplayName("Should create DC successfully without parent")
    void testCreateDC_Success() {
        // Given
        FacilityCreateRequest request = FacilityCreateRequest.builder()
                .type(FacilityType.DC)
                .name("New Distribution Center")
                .parentId(null)
                .address("New Address")
                .build();

        when(facilityRepository.findMaxDcNumber()).thenReturn(1);
        when(facilityRepository.existsByCode(anyString())).thenReturn(false);
        when(facilityRepository.save(any(Facility.class))).thenAnswer(invocation -> {
            Facility facility = invocation.getArgument(0);
            facility.setId(10L);
            facility.setCreatedAt(LocalDateTime.now());
            facility.setStatus("ACTIVE");
            return facility;
        });

        // When
        FacilityResponse result = facilityService.create(request);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getCode()).isEqualTo("DC-002");
        assertThat(result.getType()).isEqualTo(FacilityType.DC);
        assertThat(result.getName()).isEqualTo("New Distribution Center");
        verify(facilityRepository).save(any(Facility.class));
    }

    @Test
    @DisplayName("Should throw exception when creating DC with parent")
    void testCreateDC_WithParent_ShouldFail() {
        // Given
        FacilityCreateRequest request = FacilityCreateRequest.builder()
                .type(FacilityType.DC)
                .name("Invalid DC")
                .parentId(1L)  // DC cannot have parent
                .build();

        // When/Then
        assertThatThrownBy(() -> facilityService.create(request))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Distribution Center (DC) cannot have a parent");

        verify(facilityRepository, never()).save(any(Facility.class));
    }

    @Test
    @DisplayName("Should create WH successfully with DC parent")
    void testCreateWH_Success() {
        // Given
        FacilityCreateRequest request = FacilityCreateRequest.builder()
                .type(FacilityType.WH)
                .name("New Warehouse")
                .parentId(1L)  // DC parent
                .region("C")
                .address("Warehouse Address")
                .build();

        when(facilityRepository.findById(1L)).thenReturn(Optional.of(dcFacility));
        when(facilityRepository.findMaxWhNumberByRegion("WH-C-")).thenReturn(1);
        when(facilityRepository.existsByCode(anyString())).thenReturn(false);
        when(facilityRepository.save(any(Facility.class))).thenAnswer(invocation -> {
            Facility facility = invocation.getArgument(0);
            facility.setId(20L);
            facility.setCreatedAt(LocalDateTime.now());
            facility.setStatus("ACTIVE");
            return facility;
        });

        // When
        FacilityResponse result = facilityService.create(request);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getCode()).isEqualTo("WH-C-002");
        assertThat(result.getType()).isEqualTo(FacilityType.WH);
        assertThat(result.getParentId()).isEqualTo(1L);
        verify(facilityRepository).save(any(Facility.class));
    }

    @Test
    @DisplayName("Should throw exception when creating WH without parent")
    void testCreateWH_WithoutParent_ShouldFail() {
        // Given
        FacilityCreateRequest request = FacilityCreateRequest.builder()
                .type(FacilityType.WH)
                .name("Invalid Warehouse")
                .parentId(null)  // WH must have parent
                .region("C")
                .build();

        // When/Then
        assertThatThrownBy(() -> facilityService.create(request))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Warehouse (WH) must have a parent Distribution Center");

        verify(facilityRepository, never()).save(any(Facility.class));
    }

    @Test
    @DisplayName("Should throw exception when creating WH with non-DC parent")
    void testCreateWH_WithNonDCParent_ShouldFail() {
        // Given
        FacilityCreateRequest request = FacilityCreateRequest.builder()
                .type(FacilityType.WH)
                .name("Invalid Warehouse")
                .parentId(2L)  // WH parent (should be DC)
                .region("C")
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(whFacility));

        // When/Then
        assertThatThrownBy(() -> facilityService.create(request))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Warehouse parent must be a Distribution Center (DC)");

        verify(facilityRepository, never()).save(any(Facility.class));
    }

    @Test
    @DisplayName("Should create PP successfully with WH parent")
    void testCreatePP_Success() {
        // Given
        FacilityCreateRequest request = FacilityCreateRequest.builder()
                .type(FacilityType.PP)
                .name("New Pickup Point")
                .parentId(2L)  // WH parent
                .address("PP Address")
                .build();

        when(facilityRepository.findById(2L)).thenReturn(Optional.of(whFacility));
        when(facilityRepository.findMaxPpNumberByWarehouse("PP-C-001-")).thenReturn(1);
        when(facilityRepository.existsByCode(anyString())).thenReturn(false);
        when(facilityRepository.save(any(Facility.class))).thenAnswer(invocation -> {
            Facility facility = invocation.getArgument(0);
            facility.setId(30L);
            facility.setCreatedAt(LocalDateTime.now());
            facility.setStatus("ACTIVE");
            return facility;
        });

        // When
        FacilityResponse result = facilityService.create(request);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getCode()).isEqualTo("PP-C-001-02");
        assertThat(result.getType()).isEqualTo(FacilityType.PP);
        assertThat(result.getParentId()).isEqualTo(2L);
        verify(facilityRepository).save(any(Facility.class));
    }

    @Test
    @DisplayName("Should find facilities by type")
    void testFindByType() {
        // Given
        List<Facility> warehouses = Arrays.asList(whFacility);
        when(facilityRepository.findByType(FacilityType.WH)).thenReturn(warehouses);

        // When
        List<FacilityResponse> result = facilityService.findByType(FacilityType.WH);

        // Then
        assertThat(result).hasSize(1);
        assertThat(result.get(0).getType()).isEqualTo(FacilityType.WH);
        verify(facilityRepository).findByType(FacilityType.WH);
    }

    @Test
    @DisplayName("Should validate hierarchy for DC - parentId must be null")
    void testValidateHierarchy_DC() {
        // When/Then - DC with null parent should pass
        facilityService.validateHierarchy(FacilityType.DC, null);

        // When/Then - DC with non-null parent should fail
        assertThatThrownBy(() -> facilityService.validateHierarchy(FacilityType.DC, 1L))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Distribution Center (DC) cannot have a parent");
    }

    @Test
    @DisplayName("Should validate hierarchy for WH - parentId must be DC")
    void testValidateHierarchy_WH() {
        // Given
        when(facilityRepository.findById(1L)).thenReturn(Optional.of(dcFacility));

        // When/Then - WH with DC parent should pass
        facilityService.validateHierarchy(FacilityType.WH, 1L);

        // When/Then - WH without parent should fail
        assertThatThrownBy(() -> facilityService.validateHierarchy(FacilityType.WH, null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Warehouse (WH) must have a parent Distribution Center");
    }

    @Test
    @DisplayName("Should validate hierarchy for PP - parentId must be WH")
    void testValidateHierarchy_PP() {
        // Given
        when(facilityRepository.findById(2L)).thenReturn(Optional.of(whFacility));

        // When/Then - PP with WH parent should pass
        facilityService.validateHierarchy(FacilityType.PP, 2L);

        // When/Then - PP without parent should fail
        assertThatThrownBy(() -> facilityService.validateHierarchy(FacilityType.PP, null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Pickup Point (PP) must have a parent Warehouse");
    }

    @Test
    @DisplayName("Should generate DC code correctly")
    void testGenerateCode_DC() {
        // Given - first DC
        when(facilityRepository.findMaxDcNumber()).thenReturn(null);

        // When
        String code = facilityService.generateCode(FacilityType.DC, null, null);

        // Then
        assertThat(code).isEqualTo("DC-001");

        // Given - second DC
        when(facilityRepository.findMaxDcNumber()).thenReturn(1);

        // When
        code = facilityService.generateCode(FacilityType.DC, null, null);

        // Then
        assertThat(code).isEqualTo("DC-002");
    }

    @Test
    @DisplayName("Should generate WH code correctly")
    void testGenerateCode_WH() {
        // Given - first WH in region C
        when(facilityRepository.findMaxWhNumberByRegion("WH-C-")).thenReturn(null);

        // When
        String code = facilityService.generateCode(FacilityType.WH, "C", null);

        // Then
        assertThat(code).isEqualTo("WH-C-001");

        // Given - second WH in region C
        when(facilityRepository.findMaxWhNumberByRegion("WH-C-")).thenReturn(1);

        // When
        code = facilityService.generateCode(FacilityType.WH, "C", null);

        // Then
        assertThat(code).isEqualTo("WH-C-002");
    }

    @Test
    @DisplayName("Should generate PP code correctly")
    void testGenerateCode_PP() {
        // Given
        when(facilityRepository.findById(2L)).thenReturn(Optional.of(whFacility));
        when(facilityRepository.findMaxPpNumberByWarehouse("PP-C-001-")).thenReturn(null);

        // When
        String code = facilityService.generateCode(FacilityType.PP, null, 2L);

        // Then
        assertThat(code).isEqualTo("PP-C-001-01");

        // Given - second PP for same WH
        when(facilityRepository.findMaxPpNumberByWarehouse("PP-C-001-")).thenReturn(1);

        // When
        code = facilityService.generateCode(FacilityType.PP, null, 2L);

        // Then
        assertThat(code).isEqualTo("PP-C-001-02");
    }
}
