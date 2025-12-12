package com.warehouse.service;

import com.warehouse.dto.PageResponse;
import com.warehouse.model.Product;
import com.warehouse.repository.ProductRepository;
import io.micrometer.core.instrument.Counter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class ProductService {

    private final ProductRepository productRepository;
    private final Counter productsCreatedCounter;
    private final Counter productsDeletedCounter;
    private final AuditService auditService;  // nullable если Kafka недоступна
    private final StockNotificationService stockNotificationService;  // nullable если Kafka недоступна
    private final StockService stockService;  // nullable, WH-270: Stock separation

    public ProductService(ProductRepository productRepository,
                          @Qualifier("productsCreatedCounter") Counter productsCreatedCounter,
                          @Qualifier("productsDeletedCounter") Counter productsDeletedCounter,
                          @Autowired(required = false) AuditService auditService,
                          @Autowired(required = false) StockNotificationService stockNotificationService,
                          @Autowired(required = false) StockService stockService) {
        this.productRepository = productRepository;
        this.productsCreatedCounter = productsCreatedCounter;
        this.productsDeletedCounter = productsDeletedCounter;
        this.auditService = auditService;
        this.stockNotificationService = stockNotificationService;
        this.stockService = stockService;
    }

    private String getCurrentUsername() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return auth != null ? auth.getName() : "anonymous";
    }

    @CacheEvict(value = {"products", "productsByCategory"}, allEntries = true)
    public Product createProduct(Product product) {
        Product saved = productRepository.save(product);
        productsCreatedCounter.increment();
        log.info("Product created, cache evicted: {}", saved.getName());

        // Kafka: audit log (only if Kafka available)
        if (auditService != null) {
            auditService.logProductCreate(saved.getId(), saved.getName(), getCurrentUsername());
        }
        // Kafka: check stock notification (only if Kafka available)
        if (stockNotificationService != null) {
            stockNotificationService.checkAndNotify(saved);
        }

        return saved;
    }

    @Cacheable(value = "products", key = "#pageable.pageNumber + '-' + #pageable.pageSize")
    public PageResponse<Product> getAllProducts(Pageable pageable) {
        log.info("Fetching products page {} from database (cache miss)", pageable.getPageNumber());
        return PageResponse.from(productRepository.findAll(pageable));
    }

    @Cacheable(value = "productsByCategory", key = "#category + '-' + #pageable.pageNumber + '-' + #pageable.pageSize")
    public PageResponse<Product> getProductsByCategory(String category, Pageable pageable) {
        log.info("Fetching products by category from database (cache miss): {}", category);
        return PageResponse.from(productRepository.findByCategory(category, pageable));
    }

    public Product getProductById(Long id) {
        return productRepository.findById(id).orElse(null);
    }

    @CacheEvict(value = {"products", "productsByCategory"}, allEntries = true)
    public Product updateProduct(Long id, Product product) {
        Product existing = productRepository.findById(id).orElse(null);
        if (existing == null) {
            return null;
        }
        existing.setName(product.getName());
        existing.setQuantity(product.getQuantity());
        existing.setPrice(product.getPrice());
        existing.setDescription(product.getDescription());
        existing.setCategory(product.getCategory());
        Product updated = productRepository.save(existing);
        log.info("Product updated, cache evicted: {}", updated.getName());

        // Kafka: audit log (only if Kafka available)
        if (auditService != null) {
            auditService.logProductUpdate(updated.getId(), updated.getName(), getCurrentUsername());
        }
        // Kafka: check stock notification (only if Kafka available)
        if (stockNotificationService != null) {
            stockNotificationService.checkAndNotify(updated);
        }

        return updated;
    }

    @CacheEvict(value = {"products", "productsByCategory"}, allEntries = true)
    public void deleteProduct(Long id) {
        productRepository.deleteById(id);
        productsDeletedCounter.increment();
        log.info("Product deleted, cache evicted: id={}", id);

        // Kafka: audit log (only if Kafka available)
        if (auditService != null) {
            auditService.logProductDelete(id, getCurrentUsername());
        }
    }

    /**
     * Получить общее количество товара (deprecated, для совместимости)
     * WH-270: Используй StockService для работы с остатками по объектам
     * @deprecated Use StockService.getTotalStock() instead
     */
    @Deprecated
    public Integer getProductQuantity(Long productId) {
        if (stockService != null) {
            return stockService.getTotalStock(productId);
        }
        // Fallback на старое поле
        return productRepository.findById(productId)
                .map(Product::getQuantity)
                .orElse(0);
    }
}
