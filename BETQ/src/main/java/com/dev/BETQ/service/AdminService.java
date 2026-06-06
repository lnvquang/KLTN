package com.dev.BETQ.service;

import com.dev.BETQ.dto.response.*;
import com.dev.BETQ.entity.CustomerReview;
import com.dev.BETQ.entity.User;
import com.dev.BETQ.exception.AppException;
import com.dev.BETQ.exception.ErrorCode;
import com.dev.BETQ.repository.CustomerReviewRepository;
import com.dev.BETQ.repository.UserRepository;
import jakarta.transaction.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AdminService {
        @Autowired
        private UserRepository userRepository;
        @Autowired
        private CustomerReviewRepository customerReviewRepository;

        public PageResponse<UserResponse> getUsers(
                        int page,
                        int size,
                        String keyword) {
                Pageable pageable = PageRequest.of(page, size);
                Page<User> userPage;
                if (keyword == null || keyword.isBlank()) {
                        userPage = userRepository.findByRole("CUSTOMER", pageable);
                } else {
                        userPage = userRepository
                                        .findCustomers(
                                                        "CUSTOMER",
                                                        keyword,
                                                        pageable);
                }

                List<UserResponse> users = userPage.getContent()
                                .stream()
                                .map(user -> UserResponse.builder()
                                                .id(user.getId())
                                                .firstName(user.getFirstName())
                                                .lastName(user.getLastName())
                                                .email(user.getEmail())
                                                .phone(user.getPhone())
                                                .role(user.getRole())
                                                .status(user.getStatus())
                                                .createdAt(user.getCreatedAt())
                                                .build())
                                .toList();

                return PageResponse.<UserResponse>builder()
                                .content(users)
                                .page(userPage.getNumber())
                                .size(userPage.getSize())
                                .totalElements(userPage.getTotalElements())
                                .totalPages(userPage.getTotalPages())
                                .last(userPage.isLast())
                                .build();
        }

        public DashboardResponse getDashboard() {

                return DashboardResponse.builder()
                                .totalUsers(
                                                userRepository.countByRole("CUSTOMER"))
                                .totalReviews(
                                                customerReviewRepository.count())
                                .positiveReviews(
                                                customerReviewRepository.countPositiveReviews())
                                .neutralReviews(
                                                customerReviewRepository.countNeutralReviews())
                                .negativeReviews(
                                                customerReviewRepository.countNegativeReviews())
                                .build();
        }

        public BigFiveCountsResponse getBigFiveCounts() {

                BigFiveCountsResponse result = customerReviewRepository.getBigFiveStatistics();
                return BigFiveCountsResponse.builder()
                                .openness(
                                                result.getOpenness())
                                .conscientiousness(
                                                result.getConscientiousness())
                                .extraversion(
                                                result.getExtraversion())
                                .agreeableness(
                                                result.getAgreeableness())
                                .neuroticism(
                                                result.getNeuroticism())
                                .build();
        }

        public SentimentResponse getSentiment() {

                SentimentResponse result = customerReviewRepository.getSentimentStatistics();

                return SentimentResponse.builder()
                                .negative(result.getNegative())
                                .neutral(result.getNeutral())
                                .positive(result.getPositive())
                                .build();
        }

        public List<ReviewByDateResponse> getReviewStatisticsByDate() {
                return customerReviewRepository.getReviewStatisticsByDate();
        }

        public UserDetailResponse getUserDetail(Long id) {

                User user = userRepository.findById(id)
                                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));

                List<ReviewSummaryResponse> reviews = user.getReviews()
                                .stream()
                                .map(review -> ReviewSummaryResponse.builder()
                                                .id(review.getId())
                                                .reviewText(review.getReviewText())
                                                .sentimentPositive(review.getSentimentPositive())
                                                .clusterId(review.getClusterId())
                                                .clusterLabel(review.getClusterLabel())
                                                .createdAt(review.getCreatedAt())
                                                .build())
                                .toList();
                return UserDetailResponse.builder()
                                .id(user.getId())
                                .firstName(user.getFirstName())
                                .lastName(user.getLastName())
                                .email(user.getEmail())
                                .phone(user.getPhone())
                                .status(user.getStatus())
                                .role(user.getRole())
                                .createdAt(user.getCreatedAt())
                                .reviews(reviews)
                                .build();
        }

        public ReviewDetailResponse getReviewDetail(Long reviewId) {

                CustomerReview review = customerReviewRepository.findById(reviewId)
                                .orElseThrow(() -> new AppException(ErrorCode.REVIEW_NOTFOUND));

                return ReviewDetailResponse.builder()
                                .id(review.getId())
                                .reviewText(review.getReviewText())

                                .openness(review.getOpenness())
                                .conscientiousness(review.getConscientiousness())
                                .extraversion(review.getExtraversion())
                                .agreeableness(review.getAgreeableness())
                                .neuroticism(review.getNeuroticism())

                                .sentimentNegative(review.getSentimentNegative())
                                .sentimentNeutral(review.getSentimentNeutral())
                                .sentimentPositive(review.getSentimentPositive())

                                .helpfulnessKeyAspects(review.getHelpfulnessKeyAspects())
                                .helpfulnessAdvice(review.getHelpfulnessAdvice())
                                .helpfulnessTotal(review.getHelpfulnessTotal())

                                .clusterId(review.getClusterId())
                                .clusterLabel(review.getClusterLabel())

                                .createdAt(review.getCreatedAt())
                                .build();
        }

        public PageResponse<AdminReviewHistoryResponse> getAllReviews(
                        int page,
                        int size) {

                Pageable pageable = PageRequest.of(
                                page,
                                size,
                                Sort.by("createdAt").descending());

                Page<AdminReviewHistoryResponse> reviewPage = customerReviewRepository.getAllReviews(pageable);

                return PageResponse.<AdminReviewHistoryResponse>builder()
                                .content(reviewPage.getContent())
                                .page(reviewPage.getNumber())
                                .size(reviewPage.getSize())
                                .totalElements(reviewPage.getTotalElements())
                                .totalPages(reviewPage.getTotalPages())
                                .last(reviewPage.isLast())
                                .build();
        }

        @Transactional
        public void lockUser(Long userId) {
                User user = userRepository.findById(userId)
                                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));

                if (!user.getStatus()) {
                        throw new AppException(ErrorCode.USER_ALREADY_LOCKED);
                }

                user.setStatus(false);
                userRepository.save(user);

        }

        @Transactional
        public void unlockUser(Long userId) {
                User user = userRepository.findById(userId)
                                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_FOUND));

                if (user.getStatus()) {
                        throw new AppException(ErrorCode.USER_ALREADY_ACTIVE);
                }

                user.setStatus(true);
                userRepository.save(user);

        }
}
