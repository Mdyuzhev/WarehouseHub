package com.warehouse.service;

import com.warehouse.model.Product;
import com.warehouse.repository.ProductRepository;
import io.micrometer.core.instrument.Counter;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ProductService {

    private final ProductRepository productRepository;
    private final Counter productsCreatedCounter;
    private final Counter productsDeletedCounter;

    public ProductService(ProductRepository productRepository,
                          @Qualifier("productsCreatedCounter") Counter productsCreatedCounter,
                          @Qualifier("productsDeletedCounter") Counter productsDeletedCounter) {
        this.productRepository = productRepository;
        this.productsCreatedCounter = productsCreatedCounter;
        this.productsDeletedCounter = productsDeletedCounter;
    }

    public Product createProduct(Product product) {
        Product saved = productRepository.save(product);
        productsCreatedCounter.increment();
        return saved;
    }

    public List<Product> getAllProducts() {
        return productRepository.findAll();
    }

    public List<Product> getProductsByCategory(String category) {
        return productRepository.findByCategory(category);
    }

    public Product getProductById(Long id) {
        return productRepository.findById(id).orElse(null);
    }

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
        return productRepository.save(existing);
    }

    public void deleteProduct(Long id) {
        productRepository.deleteById(id);
        productsDeletedCounter.increment();
    }
}
