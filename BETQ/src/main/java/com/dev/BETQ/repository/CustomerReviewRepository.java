package com.dev.BETQ.repository;

import com.dev.BETQ.dto.response.*;
import com.dev.BETQ.entity.CustomerReview;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface CustomerReviewRepository
        extends JpaRepository<CustomerReview, Long> {
    List<CustomerReview> findByUser_IdOrderByCreatedAtDesc(Long userId);

    Optional<CustomerReview> findByIdAndUser_Id(
            Long reviewId,
            Long userId);

    @Query("""
                SELECT COUNT(c)
                FROM CustomerReview c
                WHERE c.sentimentPositive >= c.sentimentNeutral
                AND c.sentimentPositive >= c.sentimentNegative
            """)
    Long countPositiveReviews();

    @Query("""
                SELECT COUNT(c)
                FROM CustomerReview c
                WHERE c.sentimentNeutral >= c.sentimentPositive
                AND c.sentimentNeutral >= c.sentimentNegative
            """)
    Long countNeutralReviews();

    @Query("""
                SELECT COUNT(c)
                FROM CustomerReview c
                WHERE c.sentimentNegative >= c.sentimentPositive
                AND c.sentimentNegative >= c.sentimentNeutral
            """)
    Long countNegativeReviews();

    @Query("""
                SELECT new com.dev.BETQ.dto.response.BigFiveCountsResponse(
                    AVG(c.openness),
                    AVG(c.conscientiousness),
                    AVG(c.extraversion),
                    AVG(c.agreeableness),
                    AVG(c.neuroticism)
                )
                FROM CustomerReview c
            """)
    BigFiveCountsResponse getBigFiveStatistics();

    @Query("""
                SELECT new com.dev.BETQ.dto.response.SentimentResponse(
                    AVG(c.sentimentNegative),
                    AVG(c.sentimentNeutral),
                    AVG(c.sentimentPositive)
                )
                FROM CustomerReview c
            """)
    SentimentResponse getSentimentStatistics();

    @Query("""
                SELECT new com.dev.BETQ.dto.response.ReviewByDateResponse(
                   c.createdAt,
                    COUNT(c)
                )
                FROM CustomerReview c
                GROUP BY c.createdAt
                ORDER BY c.createdAt
            """)
    List<ReviewByDateResponse> getReviewStatisticsByDate();

    @Query("""
                SELECT new com.dev.BETQ.dto.response.AdminReviewHistoryResponse(
                    r.id,
                    u.id,
                    CONCAT(u.firstName,' ',u.lastName),
                    r.reviewText,
                    r.sentimentPositive,
                    r.clusterId,
                    r.clusterLabel,
                    r.createdAt
                )
                FROM CustomerReview r
                JOIN r.user u
            """)
    Page<AdminReviewHistoryResponse> getAllReviews(Pageable pageable);
}
