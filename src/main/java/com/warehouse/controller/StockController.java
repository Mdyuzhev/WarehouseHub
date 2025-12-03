package com.warehouse.controller;

import com.warehouse.dto.StockDTO;
import com.warehouse.service.StockService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST контроллер для управления остатками товаров
 * WH-270: Product/Stock Separation
 */
@RestController
@RequestMapping("/api/stock")
@RequiredArgsConstructor
@Tag(name = "Stock", description = "Управление остатками товаров на объектах")
public class StockController {

    private final StockService stockService;

    @GetMapping("/facility/{facilityId}")
    @Operation(summary = "Получить все остатки на объекте")
    public ResponseEntity<List<StockDTO>> getStockByFacility(@PathVariable Long facilityId) {
        return ResponseEntity.ok(stockService.getStockByFacility(facilityId));
    }

    @GetMapping("/product/{productId}")
    @Operation(summary = "Получить остатки товара на всех объектах")
    public ResponseEntity<List<StockDTO>> getStockByProduct(@PathVariable Long productId) {
        return ResponseEntity.ok(stockService.getStockByProduct(productId));
    }

    @GetMapping("/product/{productId}/facility/{facilityId}")
    @Operation(summary = "Получить остаток товара на конкретном объекте")
    public ResponseEntity<StockDTO> getStock(
            @PathVariable Long productId,
            @PathVariable Long facilityId) {
        StockDTO stock = stockService.getStock(productId, facilityId);
        if (stock == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(stock);
    }

    @GetMapping("/product/{productId}/total")
    @Operation(summary = "Получить суммарный остаток товара по всем объектам")
    public ResponseEntity<Map<String, Object>> getTotalStock(@PathVariable Long productId) {
        Integer total = stockService.getTotalStock(productId);
        return ResponseEntity.ok(Map.of(
                "productId", productId,
                "totalQuantity", total
        ));
    }

    @PostMapping("/product/{productId}/facility/{facilityId}")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'EMPLOYEE')")
    @Operation(summary = "Установить остаток товара на объекте")
    public ResponseEntity<StockDTO> setStock(
            @PathVariable Long productId,
            @PathVariable Long facilityId,
            @RequestBody Map<String, Integer> request) {
        Integer quantity = request.get("quantity");
        if (quantity == null || quantity < 0) {
            return ResponseEntity.badRequest().build();
        }
        return ResponseEntity.ok(stockService.setStock(productId, facilityId, quantity));
    }

    @PatchMapping("/product/{productId}/facility/{facilityId}/adjust")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER', 'EMPLOYEE')")
    @Operation(summary = "Изменить остаток (прибавить/отнять)")
    public ResponseEntity<StockDTO> adjustStock(
            @PathVariable Long productId,
            @PathVariable Long facilityId,
            @RequestBody Map<String, Integer> request) {
        Integer delta = request.get("delta");
        if (delta == null) {
            return ResponseEntity.badRequest().build();
        }
        return ResponseEntity.ok(stockService.adjustStock(productId, facilityId, delta));
    }

    @PostMapping("/product/{productId}/facility/{facilityId}/reserve")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    @Operation(summary = "Зарезервировать товар")
    public ResponseEntity<StockDTO> reserve(
            @PathVariable Long productId,
            @PathVariable Long facilityId,
            @RequestBody Map<String, Integer> request) {
        Integer amount = request.get("amount");
        if (amount == null || amount <= 0) {
            return ResponseEntity.badRequest().build();
        }
        return ResponseEntity.ok(stockService.reserve(productId, facilityId, amount));
    }

    @GetMapping("/facility/{facilityId}/low")
    @Operation(summary = "Получить товары с низким остатком на объекте")
    public ResponseEntity<List<StockDTO>> getLowStock(
            @PathVariable Long facilityId,
            @RequestParam(defaultValue = "10") Integer threshold) {
        return ResponseEntity.ok(stockService.getLowStock(facilityId, threshold));
    }
}
