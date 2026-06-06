package com.dev.BETQ.service;

import com.dev.BETQ.config.JwtProperties;
import com.dev.BETQ.dto.response.UserResponse;
import com.dev.BETQ.entity.User;
import com.dev.BETQ.exception.AppException;
import com.dev.BETQ.exception.ErrorCode;
import com.dev.BETQ.mapper.UserMapper;
import com.dev.BETQ.repository.UserRepository;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.SignedJWT;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Date;

@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private  JwtProperties jwtProperties;
    @Autowired
    private UserMapper mapper;

    public UserResponse getCurrentUser(String token) throws Exception {

        String jwt = token.substring(7);


        SignedJWT signedJWT = SignedJWT.parse(jwt);
        if(!signedJWT.verify(new MACVerifier(jwtProperties.getSecret()))){
            throw new AppException(ErrorCode.TOKEN_INVALID);
        }
        Date expiry = signedJWT.getJWTClaimsSet().getExpirationTime();
        if (expiry.before(new Date())) {
            throw new AppException(ErrorCode.TOKEN_EXPIRED);
        }

        Long userId = Long.parseLong(signedJWT.getJWTClaimsSet().getSubject());



        User user = userRepository.findById(userId)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));

        UserResponse userResponse=mapper.toDto(user);

        return userResponse;
    }
}
