package com.warehouse.config;

import com.warehouse.model.Role;
import com.warehouse.model.User;
import com.warehouse.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
@SuppressWarnings("null")
public class DataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) {
        if (userRepository.count() == 0) {
            log.info("Initializing default users...");

            userRepository.save(User.builder()
                    .username("superuser")
                    .password(passwordEncoder.encode("super123"))
                    .fullName("Суперпользователь")
                    .email("super@warehouse.local")
                    .role(Role.SUPER_USER)
                    .enabled(true)
                    .build());

            userRepository.save(User.builder()
                    .username("admin")
                    .password(passwordEncoder.encode("admin123"))
                    .fullName("Администратор")
                    .email("admin@warehouse.local")
                    .role(Role.ADMIN)
                    .enabled(true)
                    .build());

            userRepository.save(User.builder()
                    .username("manager")
                    .password(passwordEncoder.encode("manager123"))
                    .fullName("Менеджер склада")
                    .email("manager@warehouse.local")
                    .role(Role.MANAGER)
                    .enabled(true)
                    .build());

            userRepository.save(User.builder()
                    .username("employee")
                    .password(passwordEncoder.encode("employee123"))
                    .fullName("Сотрудник склада")
                    .email("employee@warehouse.local")
                    .role(Role.EMPLOYEE)
                    .enabled(true)
                    .build());

            log.info("Default users created successfully");
        }
    }
}
