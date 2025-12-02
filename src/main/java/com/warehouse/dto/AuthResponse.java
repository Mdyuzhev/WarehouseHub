package com.warehouse.dto;

import com.warehouse.model.FacilityType;
import com.warehouse.model.Role;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class AuthResponse {
    private String token;
    private String username;
    private String fullName;
    private Role role;

    // Facility information
    private FacilityType facilityType;
    private Long facilityId;
    private String facilityCode;
}
