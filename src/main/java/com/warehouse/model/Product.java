package com.warehouse.model;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.*;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "products")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Product entity")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Schema(description = "Unique product identifier", example = "1")
    private Long id;

    @NotBlank(message = "Name is required")
    @Schema(description = "Product name", example = "Laptop")
    private String name;

    @NotNull(message = "Quantity is required")
    @Min(value = 0, message = "Quantity must be >= 0")
    @Schema(description = "Product quantity in stock", example = "100")
    private Integer quantity;

    @NotNull(message = "Price is required")
    @Min(value = 0, message = "Price must be >= 0")
    @Schema(description = "Product price", example = "999.99")
    private Double price;
}