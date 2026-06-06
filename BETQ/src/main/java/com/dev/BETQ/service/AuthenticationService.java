package com.dev.BETQ.service;

import com.dev.BETQ.config.JwtProperties;
import com.dev.BETQ.dto.request.AuthenRequest;
import com.dev.BETQ.dto.request.RegisterRequest;
import com.dev.BETQ.dto.response.ResultLogin;
import com.dev.BETQ.dto.response.UserResponse;
import com.dev.BETQ.entity.RefreshToken;
import com.dev.BETQ.entity.User;
import com.dev.BETQ.exception.AppException;
import com.dev.BETQ.exception.ErrorCode;
import com.dev.BETQ.mapper.UserMapper;
import com.dev.BETQ.repository.RefreshTokenRepository;
import com.dev.BETQ.repository.UserRepository;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.JWSSigner;
import com.nimbusds.jose.crypto.MACSigner;

import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.UUID;

@Service
public class AuthenticationService {
    @Autowired
    private UserRepository repository;
    @Autowired
    private RefreshTokenRepository refreshTokenRepository;
    @Autowired
    private JwtProperties jwtProperties;
    @Autowired
    private PasswordEncoder passwordEncoder;
    @Autowired
    private UserMapper mapper;

    public String generateAccessToken(User user) throws Exception {

        JWSHeader header = new JWSHeader(JWSAlgorithm.HS512);

        JWTClaimsSet claimsSet = new JWTClaimsSet.Builder()
                .subject(user.getId().toString())
                .jwtID(UUID.randomUUID().toString())
                .claim("role", user.getRole())
                .issueTime(new Date())
                .expirationTime(
                        new Date(System.currentTimeMillis() + jwtProperties.getAccessExpire()))
                .build();

        JWSSigner signer = new MACSigner(jwtProperties.getSecret());

        SignedJWT signedJWT = new SignedJWT(
                header,
                claimsSet);

        signedJWT.sign(signer);
        return signedJWT.serialize();
    }

    public String generateRefreshToken(User user, long refreshExpire) throws Exception {

        JWSHeader header = new JWSHeader(JWSAlgorithm.HS512);

        JWTClaimsSet claimsSet = new JWTClaimsSet.Builder()
                .subject(user.getId().toString())
                .jwtID(UUID.randomUUID().toString())
                .issueTime(new Date())
                .expirationTime(
                        new Date(System.currentTimeMillis() + refreshExpire))
                .build();

        JWSSigner signer = new MACSigner(jwtProperties.getSecret());

        SignedJWT signedJWT = new SignedJWT(
                header,
                claimsSet);

        signedJWT.sign(signer);
        return signedJWT.serialize();
    }

    public ResultLogin login(AuthenRequest request) throws Exception {

        User user = repository.findByEmail(request.getEmail())
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));

        if (!user.getStatus()) {
            throw new AppException(ErrorCode.USER_ALREADY_LOCKED);
        }

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new AppException(ErrorCode.UNAUTHORIZED);
        }

        User saved = repository.save(user);
        long refreshExpire = jwtProperties.getRefreshExpire();
        RefreshToken refreshToken = RefreshToken.builder()
                .user(saved)
                .expiresAt(
                        new Date(System.currentTimeMillis() + refreshExpire))
                .revoked(false)
                .build();

        String accessToken = generateAccessToken(saved);
        String refreshTokenJwt = generateRefreshToken(saved, refreshExpire);
        refreshToken.setToken(refreshTokenJwt);
        refreshTokenRepository.save(refreshToken);
        return ResultLogin.builder()
                .accessToken(accessToken)
                .refreshToken(refreshTokenJwt)
                .refreshExpire(refreshExpire)
                .build();
    }

    public UserResponse register(RegisterRequest request) {

        if (repository.existsByEmail(request.getEmail())) {
            throw new AppException(ErrorCode.USER_EXISTED);
        }

        User user = User.builder()
                .email(request.getEmail())
                .phone(request.getPhone())
                .firstName(request.getFirstname())
                .lastName(request.getLastname())
                .password(passwordEncoder.encode(request.getPassword()))
                .createdAt(new Date())
                .role("CUSTOMER")
                .status(true)
                .build();

        User saved = repository.save(user);
        return mapper.toDto(saved);
    }

    @Transactional
    public void logout(String accessToken, String refreshToken) throws Exception {
        if (refreshToken == null || refreshToken.isBlank()) {
            return;
        }

        SignedJWT jwtRefresh = SignedJWT.parse(refreshToken);
        if (!jwtRefresh.verify(new MACVerifier(jwtProperties.getSecret()))) {
            throw new AppException(ErrorCode.TOKEN_INVALID);
        }


        if (accessToken != null && accessToken.startsWith("Bearer ")) {
            try {
                SignedJWT jwt = SignedJWT.parse(accessToken.substring(7));
                if (!jwt.verify(new MACVerifier(jwtProperties.getSecret()))) {

                }
            } catch (Exception e) {

            }
        }

        RefreshToken tokenEntity = refreshTokenRepository.findByToken(refreshToken)
                .orElseThrow(() -> new AppException(ErrorCode.TOKEN_NOT_FOUND));

        if (tokenEntity.getRevoked()) {
            throw new AppException(ErrorCode.TOKEN_REVOKED);
        }
        refreshTokenRepository.revokeByToken(refreshToken);

    }

    @Transactional
    public ResultLogin refresh(String refreshToken) throws Exception {
        if (refreshToken == null || refreshToken.isBlank()) {
            throw new AppException(ErrorCode.TOKEN_NOT_FOUND);
        }
        SignedJWT jwt = SignedJWT.parse(refreshToken);

        if (!jwt.verify(new MACVerifier(jwtProperties.getSecret()))) {
            throw new AppException(ErrorCode.TOKEN_INVALID);
        }

        Date expiry = jwt.getJWTClaimsSet().getExpirationTime();

        if (expiry.before(new Date())) {
            throw new AppException(ErrorCode.TOKEN_EXPIRED);
        }

        Long userId = Long.parseLong(jwt.getJWTClaimsSet().getSubject());
        long ttl = Math.max((expiry.getTime() - System.currentTimeMillis()) / 1000, 0);

        RefreshToken refreshTokenEntity = refreshTokenRepository.findByToken(refreshToken)
                .orElseThrow(() -> new AppException(ErrorCode.TOKEN_NOT_FOUND));

        User user = refreshTokenEntity.getUser();

        if (user != null && Boolean.FALSE.equals(user.getStatus())) {
            throw new AppException(ErrorCode.ACCOUNT_LOCKED);
        }

        refreshTokenEntity.setRevoked(true);
        refreshTokenRepository.save(refreshTokenEntity);

        long refreshExpire = jwtProperties.getRefreshExpire();

        String newAccess = generateAccessToken(user);

        String newRefresh = generateRefreshToken(user, refreshExpire);

        RefreshToken newToken = RefreshToken.builder()
                .user(user)
                .token(newRefresh)
                .expiresAt(new Date(System.currentTimeMillis() + refreshExpire))
                .revoked(false)
                .build();

        refreshTokenRepository.save(newToken);

        refreshTokenRepository.save(refreshTokenEntity);

        return ResultLogin.builder()
                .accessToken(newAccess)
                .refreshToken(newRefresh)
                .refreshExpire(refreshExpire)
                .build();
    }

}
