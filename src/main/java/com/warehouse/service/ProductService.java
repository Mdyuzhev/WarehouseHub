package com.warehouse.service;

import com.warehouse.model.Product;
import com.warehouse.repository.ProductRepository;
import io.micrometer.core.instrument.Counter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@Slf4j
public class ProductService {

    private final ProductRepository productRepository;
    private final Counter productsCreatedCounter;
    private final Counter productsDeletedCounter;
    private final AuditService auditService;
    private final StockNotificationService stockNotificationService;

    public ProductService(ProductRepository productRepository,
                          @Qualifier("productsCreatedCounter") Counter productsCreatedCounter,
                          @Qualifier("productsDeletedCounter") Counter productsDeletedCounter,
                          AuditService auditService,
                          StockNotificationService stockNotificationService) {
        this.productRepository = productRepository;
        this.productsCreatedCounter = productsCreatedCounter;
        this.productsDeletedCounter = productsDeletedCounter;
        this.auditService = auditService;
        this.stockNotificationService = stockNotificationService;
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

        // Kafka: audit log
        auditService.logProductCreate(saved.getId(), saved.getName(), getCurrentUsername());
        // Kafka: check stock notification
        stockNotificationService.checkAndNotify(saved);

        return saved;
    }

    @Cacheable(value = "products")
    public List<Product> getAllProducts() {
        log.info("Fetching all products from database (cache miss)");
        return productRepository.findAll();
    }

    @Cacheable(value = "productsByCategory", key = "#category")
    public List<Product> getProductsByCategory(String category) {
        log.info("Fetching products by category from database (cache miss): {}", category);
        return productRepository.findByCategory(category);
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

        // Kafka: audit log
        auditService.logProductUpdate(updated.getId(), updated.getName(), getCurrentUsername());
        // Kafka: check stock notification
        stockNotificationService.checkAndNotify(updated);

        return updated;
    }

    @CacheEvict(value = {"products", "productsByCategory"}, allEntries = true)
    public void deleteProduct(Long id) {
        productRepository.deleteById(id);
        productsDeletedCounter.increment();
        log.info("Product deleted, cache evicted: id={}", id);

        // Kafka: audit log
        auditService.logProductDelete(id, getCurrentUsername());
    }
}
