package com.warehouse;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class WarehouseApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(WarehouseApiApplication.class, args);
    }

}
