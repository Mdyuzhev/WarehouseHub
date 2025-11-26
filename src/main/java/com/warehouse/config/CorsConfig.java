package com.warehouse.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

import java.util.Arrays;

@Configuration
public class CorsConfig {

    @Bean
    public CorsFilter corsFilter() {
        CorsConfiguration config = new CorsConfiguration();

        // Разрешённые origins
        config.setAllowedOrigins(Arrays.asList(
            "http://localhost:3000",           // Vue dev server
            "http://192.168.1.74:30000",       // Frontend NodePort
            "http://warehouse.local"            // Production Ingress
        ));

        // Разрешённые методы
        config.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));

        // Разрешённые заголовки
        config.setAllowedHeaders(Arrays.asList("*"));

        // Разрешить credentials
        config.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);

        return new CorsFilter(source);
    }
}
