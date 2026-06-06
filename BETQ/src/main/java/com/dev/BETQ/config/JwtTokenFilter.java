package com.dev.BETQ.config;

import com.dev.BETQ.entity.User;
import com.dev.BETQ.exception.AppException;
import com.dev.BETQ.exception.ErrorCode;
import com.dev.BETQ.repository.UserRepository;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.SignedJWT;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Date;
import java.util.List;

@Component
public class JwtTokenFilter extends OncePerRequestFilter {

    @Autowired
    private JwtProperties jwtProperties;
    @Autowired
    private UserRepository userRepository;



    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        String path = request.getRequestURI();

        if (path.startsWith("/api/auth")) {
            filterChain.doFilter(request, response);
            return;
        }

        String authHeader = request.getHeader("Authorization");

        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        String token = authHeader.substring(7);

        try {
            SignedJWT jwt = SignedJWT.parse(token);

            if (!jwt.verify(new MACVerifier(jwtProperties.getSecret()))) {
                SecurityContextHolder.clearContext();
                handleError(response, ErrorCode.TOKEN_INVALID);
                return;
            }

            Date expiry = jwt.getJWTClaimsSet().getExpirationTime();
            if (expiry.before(new Date())) {
                SecurityContextHolder.clearContext();
                handleError(response, ErrorCode.TOKEN_EXPIRED);
                return;
            }


            String subject = jwt.getJWTClaimsSet().getSubject();
            if (subject == null) {
                SecurityContextHolder.clearContext();
                handleError(response, ErrorCode.UNAUTHORIZED);
                return;
            }

            Long userId = Long.parseLong(subject);
            User user=userRepository.findById(userId).orElseThrow(
                    ()->new AppException(ErrorCode.USER_NOT_FOUND)
            );
            if(user.getStatus()==false){
                SecurityContextHolder.clearContext();
                handleError(response, ErrorCode.ACCOUNT_LOCKED);
                return;
            }


            String role = jwt.getJWTClaimsSet().getStringClaim("role");
            if (role == null) {
                SecurityContextHolder.clearContext();
                handleError(response, ErrorCode.UNAUTHORIZED);
                return;
            }





            UsernamePasswordAuthenticationToken authenticationToken =
                    new UsernamePasswordAuthenticationToken(
                            userId,
                            null,
                            List.of(new SimpleGrantedAuthority("ROLE_" + role))
                    );

            SecurityContextHolder.getContext().setAuthentication(authenticationToken);

        } catch (Exception e) {
            SecurityContextHolder.clearContext();
            handleError(response, ErrorCode.UNAUTHORIZED);
            return;
        }

        filterChain.doFilter(request, response);
    }

    private void handleError(HttpServletResponse response, ErrorCode error) throws IOException {
        response.setStatus(error.getStatus());
        response.setContentType("application/json;charset=UTF-8");

        String json = String.format("""
                {
                    "status":%s,
                    "code": "%s",
                    "message": "%s"
                }
                """,error.getStatus(), error.getCode(), error.getMessage());

        response.getWriter().write(json);
        response.getWriter().flush();
    }
}