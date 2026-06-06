package com.dev.BETQ.repository;


import com.dev.BETQ.entity.RefreshToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken,String> {

    Optional<RefreshToken> findByTokenAndRevokedFalse(String token);

    @Modifying
    @Query("update RefreshToken r set r.revoked = true where r.token = :token")
    void revokeByToken(String token);

    @Modifying
    @Query("update RefreshToken r set r.revoked = true where r.user.id = :userId")
    void revokeAllByUserId(Long userId);

    Optional<RefreshToken> findByToken(String token);

}
