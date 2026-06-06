package com.dev.BETQ.controller;

import com.dev.BETQ.dto.response.*;
import com.dev.BETQ.service.AdminService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/admin")
public class AdminController {
        @Autowired
        private AdminService adminService;

        @PreAuthorize("hasRole('ADMIN')")
        @GetMapping("/users")
        public ApiResponse<PageResponse<UserResponse>> getUsers(

                        @RequestParam(defaultValue = "0") int page,

                        @RequestParam(defaultValue = "5") int size,

                        @RequestParam(required = false) String keyword) {

                return ApiResponse.<PageResponse<UserResponse>>builder()
                                .status(200)
                                .message("Lay danh sach user thanh cong")
                                .result(adminService.getUsers(page, size, keyword))
                                .build();
        }

        @PreAuthorize("hasRole('ADMIN')")
        @GetMapping("/dashboard")
        public ApiResponse<DashboardResponse> getDashboard() {
                return ApiResponse.<DashboardResponse>builder()
                                .status(200)
                                .message("Lay dashboard thanh cong")
                                .result(adminService.getDashboard())
                                .build();
        }

        @PreAuthorize("hasRole('ADMIN')")
        @GetMapping("/statistics/sentiment")
        public ApiResponse<SentimentResponse> getSentiment() {
                return ApiResponse.<SentimentResponse>builder()
                                .status(200)
                                .message("Lay sentiment thanh cong")
                                .result(adminService.getSentiment())
                                .build();
        }

        @PreAuthorize("hasRole('ADMIN')")
        @GetMapping("/statistics/personality")
        public ApiResponse<BigFiveCountsResponse> getBigFive() {
                return ApiResponse.<BigFiveCountsResponse>builder()
                                .status(200)
                                .message("Lay big five thanh cong")
                                .result(adminService.getBigFiveCounts())
                                .build();
        }

        @PreAuthorize("hasRole('ADMIN')")
        @GetMapping("/statistics/reviews-by-date")
        public ApiResponse<List<ReviewByDateResponse>> getReviewsByDate() {
                return ApiResponse.<List<ReviewByDateResponse>>builder()
                                .status(200)
                                .message("Lay bieu do thoi gian tao review")
                                .result(adminService.getReviewStatisticsByDate())
                                .build();
        }

        @PreAuthorize("hasRole('ADMIN')")
        @GetMapping("/user/detail/{id}")
        public ApiResponse<UserDetailResponse> getUserDetail(
                        @PathVariable Long id) {

                return ApiResponse.<UserDetailResponse>builder()
                                .status(200)
                                .message("lay chi tiet nguoi dung thanh cong")
                                .result(adminService.getUserDetail(id))
                                .build();
        }

        @PreAuthorize("hasRole('ADMIN')")
        @GetMapping("/reviews/{reviewId}")
        public ApiResponse<ReviewDetailResponse> getReviewDetail(
                        @PathVariable Long reviewId) {

                return ApiResponse.<ReviewDetailResponse>builder()
                                .result(adminService.getReviewDetail(reviewId))
                                .build();
        }

        @GetMapping("/reviews")
        public ApiResponse<PageResponse<AdminReviewHistoryResponse>> getAllReviews(
                        @RequestParam(defaultValue = "0") int page,
                        @RequestParam(defaultValue = "5") int size) {
                return ApiResponse.<PageResponse<AdminReviewHistoryResponse>>builder()
                                .result(adminService.getAllReviews(page, size))
                                .build();
        }
    @PutMapping("/lock")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Void> lock(@RequestParam Long userId) {
        adminService.lockUser(userId);
        return ApiResponse.<Void>builder()
                .status(200)
                .message("Đã khóa thành công")
                .build();
    }

    @PutMapping("/unlock")
    @PreAuthorize("hasRole('ADMIN')")
    public ApiResponse<Void> unlock(@RequestParam Long userId) {
        adminService.unlockUser(userId);
        return ApiResponse.<Void>builder()
                .status(200)
                .message("Đã kích hoạt thành công")
                .build();
    }
}
