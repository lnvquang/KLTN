package com.dev.BETQ.controller;

import com.dev.BETQ.dto.response.ApiResponse;
import com.dev.BETQ.dto.response.UserResponse;
import com.dev.BETQ.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/user")
public class UserController {
    @Autowired
    private UserService userService;
    @GetMapping("/me")
    public ApiResponse<UserResponse>getCurrentUser(@RequestHeader("Authorization") String token) throws Exception{
        return ApiResponse.<UserResponse>builder()
                .status(200)
                .message("Lấy thông tin hiện tại thành công")
                .result(userService.getCurrentUser(token))
                .build();
    }
}
