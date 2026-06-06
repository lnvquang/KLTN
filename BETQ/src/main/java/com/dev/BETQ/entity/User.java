package com.dev.BETQ.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;
import java.util.List;

@Entity
@Table(name = "users")
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Data
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(length = 255,unique = true)
    private String email;
    @Column(length = 255,unique = true)
    private String phone;
    private String password;
    @Column(length = 50)
    private String firstName;
    @Column(length = 50)
    private String lastName;
    @Column(length = 50)
    private String address;
    private Boolean status;
    private String role;
    private Date createdAt;
    @OneToMany(mappedBy = "user")
    private List<CustomerReview> reviews;
}
