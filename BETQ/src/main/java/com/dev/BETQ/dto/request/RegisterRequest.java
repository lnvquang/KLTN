package com.dev.BETQ.dto.request;


import lombok.AllArgsConstructor;
import lombok.Data;


@AllArgsConstructor
@Data
public class RegisterRequest {
    private String firstname;
    private String lastname;
    private String email;
    private String phone;
    private String password;


}
