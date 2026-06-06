package com.dev.BETQ.repository;

import com.dev.BETQ.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User,Long> {
    boolean existsByEmail(String email);
    Optional<User> findByEmail(String email);
    @Query("""
    SELECT u
    FROM User u
    WHERE u.role = :role
    AND (
        LOWER(u.email) LIKE LOWER(CONCAT('%', :keyword, '%'))
        OR LOWER(u.firstName) LIKE LOWER(CONCAT('%', :keyword, '%'))
    )
""")
    Page<User> findCustomers(
            @Param("role") String role,
            @Param("keyword") String keyword,
            Pageable pageable
    );
    Page<User> findByRole(
            String role,
            Pageable pageable
    );
    Long countByRole(String role);


}
