package com.dev.BETQ.controller;

import com.dev.BETQ.dto.request.ReviewRequest;
import com.dev.BETQ.dto.response.ApiResponse;
import com.dev.BETQ.dto.response.ReviewAnalysisResponse;
import com.dev.BETQ.dto.response.ReviewDetailResponse;
import com.dev.BETQ.dto.response.ReviewHistoryResponse;
import com.dev.BETQ.service.ReviewService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/reviews")
@RequiredArgsConstructor
public class ReviewController {

    @Autowired
    private ReviewService reviewService;

    @PreAuthorize("hasRole('CUSTOMER')")
    @PostMapping("/analyze")
    public ApiResponse<ReviewAnalysisResponse> analyze(@RequestHeader("Authorization") String token,
                                                       @RequestBody ReviewRequest request
    ) throws Exception {
        return ApiResponse.<ReviewAnalysisResponse>builder()
                .status(200)
                .message("Lay analyze thanh cong")
                .result(reviewService.analyzeReview(token, request))
                .build();
    }

    @PreAuthorize("hasRole('CUSTOMER')")
    @GetMapping("/history")
    public ApiResponse<List<ReviewHistoryResponse>> getHistory(@RequestHeader("Authorization")
                                                               String token) throws Exception {
        return ApiResponse.<List<ReviewHistoryResponse>>builder()
                .status(200)
                .message("lay lịch su review thành cong")
                .result(reviewService.getHistory(token))
                .build();
    }

    @GetMapping("/history/detail")
    public ApiResponse<ReviewDetailResponse> getDetail(@RequestHeader("Authorization") String token,
                                                       @RequestParam Long id

    )throws Exception {
        return ApiResponse.<ReviewDetailResponse>builder()
                .status(200)
                .message("Lay chi tiet review")
                .result(reviewService.getDetail(token,id))
                .build();

    }
}