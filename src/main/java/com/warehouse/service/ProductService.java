package com.warehouse.service;

import com.warehouse.model.Product;
import com.warehouse.repository.ProductRepository;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ProductService {

    private final ProductRepository productRepository;
    private final Counter productsCreatedCounter;
    private final Counter productsDeletedCounter;

    public ProductService(ProductRepository productRepository, MeterRegistry registry) {
        this.productRepository = productRepository;
        this.productsCreatedCounter = Counter.builder("warehouse.products.created")
                .description("Total products created")
                .register(registry);
        this.productsDeletedCounter = Counter.builder("warehouse.products.deleted")
                .description("Total products deleted")
                .register(registry);
    }

    public Product createProduct(Product product) {
        Product saved = productRepository.save(product);
        productsCreatedCounter.increment();
        return saved;
    }

    public List<Product> getAllProducts() {
        return productRepository.findAll();
    }

    public void deleteProduct(Long id) {
        productRepository.deleteById(id);
        productsDeletedCounter.increment();
    }
}
