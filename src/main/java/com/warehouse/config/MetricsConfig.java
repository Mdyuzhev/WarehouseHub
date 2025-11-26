package com.warehouse.config;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class MetricsConfig {

    /**
     * Counter for tracking product operations
     */
    @Bean
    public Counter productsCreatedCounter(MeterRegistry registry) {
        return Counter.builder("warehouse.products.created")
                .description("Total number of products created")
                .tag("operation", "create")
                .register(registry);
    }

    @Bean
    public Counter productsDeletedCounter(MeterRegistry registry) {
        return Counter.builder("warehouse.products.deleted")
                .description("Total number of products deleted")
                .tag("operation", "delete")
                .register(registry);
    }

    /**
     * Timer for tracking API response times
     */
    @Bean
    public Timer productApiTimer(MeterRegistry registry) {
        return Timer.builder("warehouse.api.products.timer")
                .description("Time spent processing product API requests")
                .register(registry);
    }
}
